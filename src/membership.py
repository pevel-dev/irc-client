import typing
from enum import Enum, IntEnum

MEMBERSHIP_PREFIXES = [
    ('~', '+q'),  # founder
    ('&', '+a'),  # protected
    ('@', '+o'),  # operator
    ('%', '+h'),  # halfop
    ('+', '+v'),
]  # voice


class ChannelMembership(IntEnum):
    FOUNDER = 0
    PROTECTED = 1
    OPERATOR = 2
    HALFOP = 3
    VOICE = 4
    DEFAULT = 5

    @staticmethod
    def parse_name(name: str) -> typing.Tuple[Enum, str]:
        membership = None
        for i in range(len(MEMBERSHIP_PREFIXES)):
            for prefix in MEMBERSHIP_PREFIXES[i]:
                if name.startswith(prefix):
                    membership = ChannelMembership(i)
                    break
        if membership is None:
            membership = ChannelMembership.DEFAULT
        return membership, name
