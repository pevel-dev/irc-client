from typing import *


class Message:
    def __init__(self, command: str, parameters: Iterable[str]):
        self.command = command
        self.parameters = parameters
        ...
