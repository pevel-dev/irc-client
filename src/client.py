import asyncio
from asyncio import StreamReader, StreamWriter
from typing import *
from loguru import logger
from collections import namedtuple, deque

Channel = namedtuple('Channel', ['channel', 'client_count', 'topic'])
Command = namedtuple('Command', ['command', 'parameters'])


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
        self.commands: deque[Command] = deque()
        self.update_channel = on_update_channels

        self.checks = [self.on_ping, self.on_322, self.on_323]

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host,
                                                                 self.port)
        await self.authorize()
        await self.update_channels()

    async def handle(self):
        consume_task = asyncio.create_task(self.consume())
        produce_task = asyncio.create_task(self.produce())
        done, pending = await asyncio.wait([consume_task, produce_task],
                                           return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()

    async def consume(self):
        while True:
            try:
                data = await self.reader.readuntil(separator=b'\r\n')
                try:
                    response = data.decode(self.encoding)
                    await self.process_response(response)
                except UnicodeDecodeError:
                    ...
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

        await asyncio.sleep(0.01)

    async def on_ping(self, response: str):
        if 'PING' in response:
            self.commands.append(
                Command("PONG", [":" + response.split(":")[1]]))

    async def on_322(self, response: str):
        if response.split(' ')[1] == '322':
            channel, client_count, *topic = response.split(' ')[3:]
            topic = ' '.join(topic)[1:]
            self.channels.append(Channel(channel, client_count, topic))

    async def on_323(self, response: str):
        # TODO: Паша, сними комменты, когда напишешь свою функцию
        # if response.split(' ')[1] == '323':
        #   await self.update_channel(self.channels)
        ...

    async def _send_command(self, command: Command):
        message = f'{command.command} {" ".join(command.parameters)}\r\n'
        print(f'Sending {message}')
        self.writer.write(message.encode(self.encoding))
        await self.writer.drain()
        await asyncio.sleep(0.01)

    async def authorize(self):
        # TODO: send_password()
        self.commands.append(Command("NICK", [self.nickname]))
        self.commands.append(
            Command("USER", [self.nickname, "8", "*", ":Pavel Egorov"]))
        await asyncio.sleep(0.01)

    async def update_channels(self):
        self.commands.append(Command("LIST", []))
        await asyncio.sleep(0.01)

    async def join_channel(self, channel: Channel):
        self.commands.append(Command("JOIN", [channel.channel]))
        await asyncio.sleep(0.01)

    async def leave_channel(self):
        self.commands.append(Command("JOIN", ["0"]))
        await asyncio.sleep(0.01)

    async def close(self):
        self.commands.append(Command("QUIT", ["Вы долбоебы блять"]))
        await asyncio.sleep(0.01)


async def main():
    client = IrcClient("irc.ircnet.ru", 6688, 'pavlo', 'utf-8', None, None, None)
    await client.connect()
    await client.join_channel(Channel('#noxyu3M', None, None))
    await client.leave_channel()
    await client.close()
    await client.handle()


if __name__ == '__main__':
    asyncio.run(main())
