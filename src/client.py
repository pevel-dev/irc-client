import asyncio
from asyncio import StreamReader, StreamWriter
from typing import *
from message import Message
from loguru import logger
from collections import namedtuple


Channel = namedtuple('Channel', ['channel', 'client_count', 'topic'])


class IrcClient:
    def __init__(self, host, port, nickname, encoding):
        self.host = host
        self.port = port
        self.nickname = nickname
        self.encoding = encoding
        self.reader: StreamReader = None
        self.writer: StreamWriter = None

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        await self.on_connect()
        await self.listen()

        # await asyncio.wait([on_connect_task, listen_task],
        #                    return_when=asyncio.FIRST_COMPLETED)

    async def listen(self):
        while True:
            data = await self.reader.read(1024)
            try:
                text = data.decode(self.encoding)
                await self.process_response(text)
            except UnicodeDecodeError as err:
                print(data)

            await asyncio.sleep(0.01)

    async def process_response(self, response):
        if 'PING' in response:
            await self.send_command(Message("PONG", [":" + response.split(":")[1]]))
        print(response)

    async def send_command(self, message: Message):
        text = f'{message.command} {" ".join(message.parameters)}\r\n'
        print(f'Sending {text}')
        self.writer.write(text.encode(self.encoding))
        await self.writer.drain()

    async def on_connect(self):
        await asyncio.sleep(0.05)
        await self.authorize()
        await asyncio.sleep(0.05)
        await self.extract_channels()

    async def authorize(self):
        # TODO: send_password()
        await self.send_command(Message("NICK", [self.nickname]))
        await self.send_command(Message("USER", [self.nickname, "0", "*", ":Pavel Egorov"]))
        await self.send_command(Message("MODE", [self.nickname, "+i"]))

    async def extract_channels(self):
        await self.send_command(Message("LIST", []))


if __name__ == '__main__':
    client = IrcClient("irc.ircnet.ru", "6667", 'pevel', encoding='cp1251')
    asyncio.run(client.connect())
