import asyncio
import typing
from asyncio import StreamReader, StreamWriter
from collections import deque, namedtuple

from membership import ChannelMembership

Channel = namedtuple('Channel', ['channel', 'client_count', 'topic'])
Command = namedtuple('Command', ['command', 'parameters'])
Member = namedtuple('Member', ['membership', 'nick'])


class IrcClient:
    def __init__(
        self,
        host: str,
        port: str | int,
        nickname: str,
        encoding: str,
        on_update_channels: typing.Callable,
        on_update_members: typing.Callable,
        on_receiving_message: typing.Callable,
    ):
        self.host: str = host
        self.port: str | int = port
        self.nickname: str = nickname
        self.encoding: str = encoding

        self.reader: StreamReader = None
        self.writer: StreamWriter = None

        self.channels: list[Channel] = []
        self.current_channel = None
        self.members: list[Member] = None
        self.commands: deque[Command] = deque()

        self.checks = [self.on_ping, self.on_322, self.on_323, self.on_353, self.on_366]

        self.on_receiving_message = on_receiving_message
        self.on_update_members = on_update_members
        self.on_update_channels = on_update_channels

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        await self.authorize()
        await self.update_channels()

    async def handle(self):
        consume_task = asyncio.create_task(self.consume())
        produce_task = asyncio.create_task(self.produce())
        done, pending = await asyncio.wait([consume_task, produce_task], return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()

    async def consume(self):
        while True:
            try:
                data = await self.reader.readuntil(separator=b'\r\n')
                try:
                    response = data.decode(self.encoding)
                    await self.process_response(response)
                except UnicodeDecodeError as ex:
                    print('ОШИБОЧКА', ex)
            except asyncio.exceptions.IncompleteReadError:
                break
            await asyncio.sleep(0.01)

    async def produce(self):
        while True:
            if self.commands:
                command = self.commands.popleft()
                await self._send_command(command)
            await asyncio.sleep(0.01)

    async def process_response(self, response: str):
        print(response, end='')
        response = response.rstrip('\r\n')
        for check in self.checks:
            await check(response)
        await self.on_receiving_message(response)

    async def on_ping(self, response: str):
        if 'PING' in response:
            self.commands.append(Command("PONG", [":" + response.split(":")[1]]))

    # RPL_LIST
    async def on_322(self, response: str):
        if response.split(' ')[1] == '322':
            channel, client_count, *topic = response.split(' ')[3:]
            topic = ' '.join(topic)[1:]
            self.channels.append(Channel(channel, client_count, topic))

    # RPL_LISTEND
    async def on_323(self, response: str):
        if response.split(' ')[1] == '323':
            await self.on_update_channels(self.channels)

    # RPL_NAMREPLY
    async def on_353(self, response: str):
        if response.split(' ')[1] == '353':
            self.members = []
            names = response.rstrip().split(' ')[5:]
            names[0] = names[0].lstrip(':')
            for name in names:
                membership, nick = ChannelMembership.parse_name(name)
                self.members.append(Member(membership, nick))

    # RPL_ENDOFNAMES
    async def on_366(self, response: str):
        if response.split(' ')[1] == '366':
            await self.on_update_members(self.members)

    async def _send_command(self, command: Command):
        message = f'{command.command} {" ".join(command.parameters)}\r\n'
        print(f'Sending {message}')
        self.writer.write(message.encode(self.encoding))
        await self.writer.drain()

    async def authorize(self):
        # TODO: send_password()
        self.commands.append(Command("NICK", [self.nickname]))
        self.commands.append(Command("USER", [self.nickname, "8", "*", ":Pavel Egorov"]))

    async def update_channels(self):
        self.commands.append(Command("LIST", []))

    async def update_members(self, channel: Channel):
        self.commands.append(Command("NAMES", [channel.channel]))

    async def join_channel(self, channel: Channel):
        self.commands.append(Command("JOIN", [channel.channel]))
        self.current_channel = channel.channel

    async def leave_channel(self):
        self.commands.append(Command("JOIN", ["0"]))
        self.current_channel = None

    async def close(self):
        self.commands.append(Command("QUIT", ["Bye!"]))

    def send_message(self, message):
        self.commands.append(Command("PRIVMSG", [self.current_channel, ":" + message]))
