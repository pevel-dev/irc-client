import asyncio
from asyncio import StreamReader, StreamWriter
from typing import *
from loguru import logger
from collections import namedtuple, deque

Channel = namedtuple('Channel', ['channel', 'client_count', 'topic'])
Command = namedtuple('Command', ['command', 'parameters'])


class IrcClient:
    def __init__(self, host: str, port: str | int, nickname: str,
                 encoding: str):
        self.host: str = host
        self.port: str | int = port
        self.nickname: str = nickname
        self.encoding: str = encoding

        self.reader: StreamReader = None
        self.writer: StreamWriter = None

        self.channels: list[Channel] = []

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host,
                                                                 self.port)
        await self.authorize()
        await self.listen()

    async def listen(self):
        while True:
            data = await self.reader.readuntil(separator=b'\r\n')
            try:
                response = data.decode(self.encoding)
                await self.process_response(response)
            except UnicodeDecodeError:
                ...
            await asyncio.sleep(0.01)

    async def process_response(self, response: str):
        print(response, end='')
        response = response.rstrip('\r\n')
        if 'PING' in response:
            await self.send_command(
                Command("PONG", [":" + response.split(":")[1]]))
            return
        if response.split(' ')[1] == '322':
            channel, client_count, *topic = response.split(' ')[3:]
            topic = ' '.join(topic)[1:]
            self.channels.append(Channel(channel, client_count, topic))
            return
        if response.split(' ')[1] == '323':
            print(*self.channels, sep='\n')
            return

    async def send_command(self, command: Command):
        text = f'{command.command} {" ".join(command.parameters)}\r\n'
        print(f'Sending {text}')
        self.writer.write(text.encode(self.encoding))
        await self.writer.drain()
        await asyncio.sleep(0.01)

    async def authorize(self):
        # TODO: send_password()
        await self.send_command(Command("NICK", [self.nickname]))
        await self.send_command(
            Command("USER", [self.nickname, "8", "*", ":Pavel Egorov"]))
        # await self.send_command(Command("MODE", [self.nickname, "+i"]))
        await self.send_command(Command("LIST", []))

    async def join_channel(self, channel: Channel):
        await self.send_command(Command("JOIN", [channel.channel]))


if __name__ == '__main__':
    client = IrcClient("irc.ircnet.ru", 6688, 'pavlo', encoding='utf-8')
    asyncio.run(client.connect())
