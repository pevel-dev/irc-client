import asyncio
from membership import ChannelMembership
from asyncio import StreamReader, StreamWriter
from typing import *
from loguru import logger
from collections import namedtuple, deque

Channel = namedtuple('Channel', ['channel', 'client_count', 'topic'])
Command = namedtuple('Command', ['command', 'parameters'])
Member = namedtuple('Member', ['membership', 'nick'])

MAX_MESSAGE_SIZE = 384


class IrcClient:

    def __init__(self,
                 host: str, port: str | int, nickname: str, encoding: str,
                 on_update_channels: Callable,
                 on_update_members: Callable,
                 on_receiving_message: Callable):

        self.host: str = host
        self.port: str | int = port
        self.nickname: str = nickname
        self.encoding: str = encoding

        self.reader: StreamReader = None
        self.writer: StreamWriter = None

        self.channels: list[Channel] = []
        self.current_channel = None
        self.members: list[Member] = []
        self.commands: deque[Command] = deque()

        self.checks = [self._on_ping,
                       self._on_322, self._on_323,
                       self._on_353, self._on_366]

        self.on_receiving_message = on_receiving_message
        self.on_update_members = on_update_members
        self.on_update_channels = on_update_channels

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host,
                                                                 self.port)
        await self._authorize()
        await self.update_channels()

    async def handle(self):
        consume_task = asyncio.create_task(self._consume())
        produce_task = asyncio.create_task(self._produce())
        done, pending = await asyncio.wait([consume_task, produce_task],
                                           return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()

    async def _consume(self):
        while True:
            try:
                data = await self.reader.readuntil(separator=b'\r\n')
                try:
                    response = data.decode(self.encoding)
                    await self._process_response(response)
                except UnicodeDecodeError:
                    ...
            except asyncio.exceptions.IncompleteReadError:
                break
            await asyncio.sleep(0.01)

    async def _produce(self):
        while True:
            if self.commands:
                command = self.commands.popleft()
                await self._send_command(command)
            await asyncio.sleep(0.01)

    async def _process_response(self, response: str):
        logger.info(f'Getting response: {response}')
        response = response.rstrip('\r\n')
        for check in self.checks:
            await check(response)
        await self.on_receiving_message(response)

    async def _on_ping(self, response: str):
        if 'PING' in response:
            self.commands.append(
                Command("PONG", [":" + response.split(":")[1]]))

    # RPL_LIST
    async def _on_322(self, response: str):
        if response.split(' ')[1] == '322':
            channel, client_count, *topic = response.split(' ')[3:]
            topic = ' '.join(topic)[1:]
            self.channels.append(Channel(channel, client_count, topic))

    # RPL_LISTEND
    async def _on_323(self, response: str):
        if response.split(' ')[1] == '323':
            await self.on_update_channels(self.channels)

    # RPL_NAMREPLY
    async def _on_353(self, response: str):
        if response.split(' ')[1] == '353':
            self.members = []
            names = response.rstrip().split(' ')[5:]
            names[0] = names[0].lstrip(':')
            for name in names:
                membership, nick = ChannelMembership.parse_name(name)
                self.members.append(Member(membership, nick))

    # RPL_ENDOFNAMES
    async def _on_366(self, response: str):
        if response.split(' ')[1] == '366':
            await self.on_update_members(self.members)

    async def _send_command(self, command: Command):
        message = f'{command.command} {" ".join(command.parameters)}\r\n'
        logger.info(f'Sending {message}')
        self.writer.write(message.encode(self.encoding))
        await self.writer.drain()

    async def _authorize(self):
        # TODO: send_password()
        self.commands.append(Command("NICK", [self.nickname]))
        self.commands.append(
            Command("USER", [self.nickname, "8", "*", ":Pavel Egorov"]))

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
        words = deque(message.split(' '))
        whitespace_size = 1
        while words:
            block = []
            block_size = -1
            if len(words[0].encode()) <= MAX_MESSAGE_SIZE:
                while words and (block_size + whitespace_size) + len(
                        words[0].encode()) <= MAX_MESSAGE_SIZE:
                    word = words.popleft()
                    block.append(word)
                    block_size += len(word.encode()) + whitespace_size
                self.commands.append(Command("PRIVMSG",
                                             [self.current_channel,
                                              ":" + ' '.join(block)]))
            else:
                self._split_into_blocks(words.popleft())

    def _split_into_blocks(self, word):
        chars = deque(word)
        while chars:
            block = []
            block_size = 0
            while chars and block_size + len(
                    chars[0].encode()) <= MAX_MESSAGE_SIZE:
                char = chars.popleft()
                block.append(char)
                block_size += len(char.encode())
            self.commands.append(Command("PRIVMSG",
                                         [self.current_channel,
                                          ":" + ''.join(block)]))


async def main():
    client = IrcClient("irc.ircnet.ru", 6688, 'pavlo', 'utf-8',
                       None, None, None)
    await client.connect()
    # await client.join_channel(Channel('#Usue', None, None))
    # await client.update_members(Channel('#Usue', None, None))
    # await client.leave_channel()
    # await client.close()
    await client.handle()


if __name__ == '__main__':
    asyncio.run(main())
