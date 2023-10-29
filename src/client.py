import asyncio
from membership import ChannelMembership
from asyncio import StreamReader, StreamWriter
from typing import *
from loguru import logger
from collections import namedtuple, deque

Channel = namedtuple('Channel', ['channel', 'client_count', 'topic'])
Command = namedtuple('Command', ['command', 'parameters'])
Member = namedtuple('Member', ['membership', 'nick', 'prefix'])

MAX_MESSAGE_SIZE = 384


def parse_user(response: str) -> Tuple[str, str]:
    nick, full_name = response.lstrip(':').split(' ')[0].split('!')
    return nick, full_name


class IrcClient:

    def __init__(self,
                 host: str, port: str | int, nickname: str, encoding: str,
                 on_update_channels: Callable,
                 on_update_members: Callable,
                 on_receiving_message: Callable,
                 ):

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
                       self._on_353, self._on_366,
                       self._on_chat_message,
                       self._on_members_list_change,
                       ]

        self.on_receiving_message = on_receiving_message
        self.on_update_members = on_update_members
        self.on_update_channels = on_update_channels

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host,
                                                                 self.port)
        self._authorize()
        self.update_channels()

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
        logger.info(f'Getting response {response}')
        response = response.rstrip('\r\n')
        for check in self.checks:
            await check(response)

    async def _on_chat_message(self, response: str):
        if response.split(' ')[1] == 'PRIVMSG':
            nick, fullname = parse_user(response)
            message = response.split(':')[2]
            await self.on_receiving_message(f'<{nick} ({fullname})> {message}')

    async def _on_members_list_change(self, response: str):
        if response.split(' ')[1] not in ('PART', 'JOIN'):
            return
        nick, full_name = parse_user(response)
        if response.split(' ')[1] == 'PART':
            channels = response.rstrip().split(' ')[2].split(',')
            message = f'{nick} ({full_name}) has left {self.current_channel}'
            if self.current_channel in channels:
                self.members = [member for member in self.members if
                                member.nick != nick]
        if response.split(' ')[1] == 'JOIN':
            channels = response.rstrip().split(' ')[2].lstrip(':').split(',')
            message = f'{nick} ({full_name}) has joined {self.current_channel}'
            if self.current_channel in channels:
                membership, nick, prefix = ChannelMembership.parse_name(nick)
                self.members.append(Member(membership, nick, prefix))
        await self.on_update_members(sorted(self.members))
        await self.on_receiving_message(message)

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
            await self.on_update_channels(sorted(
                self.channels,
                key=lambda c: int(c.client_count),
                reverse=True
            ))

    # RPL_NAMREPLY
    async def _on_353(self, response: str):
        if response.split(' ')[1] == '353':
            self.members = []
            names = response.rstrip().split(' ')[5:]
            names[0] = names[0].lstrip(':')
            for name in names:
                membership, nick, prefix = ChannelMembership.parse_name(name)
                self.members.append(Member(membership, nick, prefix))

    # RPL_ENDOFNAMES
    async def _on_366(self, response: str):
        if response.split(' ')[1] == '366':
            await self.on_update_members(sorted(self.members))

    async def _send_command(self, command: Command):
        message = f'{command.command} {" ".join(command.parameters)}\r\n'
        logger.info(f'Sending {message}')
        self.writer.write(message.encode(self.encoding))
        await self.writer.drain()

    def _authorize(self):
        # TODO: send_password()
        self.commands.append(Command("NICK", [self.nickname]))
        self.commands.append(
            Command("USER", [self.nickname, "8", "*", ":Pavel Egorov"])
        )

    def update_channels(self):
        self.commands.append(Command("LIST", []))

    def update_members(self):
        self.commands.append(Command("NAMES", [self.current_channel]))

    def join_channel(self, channel: Channel):
        self.commands.append(Command("JOIN", [channel.channel]))
        self.current_channel = channel.channel

    def leave_channel(self):
        self.commands.append(Command("JOIN", ["0"]))
        self.current_channel = None

    def close(self):
        self.commands.append(Command("QUIT", ["Bye!"]))

    async def send_message(self, message):
        await self._send_text_by_blocks(message)

    async def _send_text_by_blocks(self, text):
        words = deque(text.split(' '))
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
                await self._send_single_message(' '.join(block))
            else:
                await self._send_word_by_blocks(words.popleft())

    async def _send_word_by_blocks(self, word):
        chars = deque(word)
        while chars:
            block = []
            block_size = 0
            while chars and block_size + len(
                    chars[0].encode()) <= MAX_MESSAGE_SIZE:
                char = chars.popleft()
                block.append(char)
                block_size += len(char.encode())
            await self._send_single_message(''.join(block))

    async def _send_single_message(self, message):
        await self.on_receiving_message(f'<{self.nickname} (YOU)> {message}')
        self.commands.append(Command("PRIVMSG",
                                     [self.current_channel,
                                      ":" + message])
                             )
