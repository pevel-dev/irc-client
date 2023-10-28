import asyncio
from websockets.sync.client import connect


class IrcClient:
    def __init__(self):
        ...

    def connect_to_server(self, host, port):
        with connect("ws://localhost:8765") as websocket:
            websocket.send("Hello world!")
            message = websocket.recv()
            print(f"Received: {message}")

    async def send_pass_message(self, password):
        ...

    async def send_nick_message(self, nickname, hop_count=None):
        ...

    async def send_user_message(self, username, hostname, servername, real_name):
        ...

    async def send_list_message(self, channels=None, server=None):
        ...

    async def send_join_message(self, channel, key):
        ...
