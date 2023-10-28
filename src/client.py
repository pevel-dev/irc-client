import asyncio
from websockets.client import *
from typing import *


class IrcClient:
    def __init__(self):
        self.websocket: WebSocketURI = None

    async def consumer_handler(self):
        async for message in self.websocket:
            await consumer(message)
