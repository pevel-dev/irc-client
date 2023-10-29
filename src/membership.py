from enum import IntEnum

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
    def parse_name(name: str) -> tuple[IntEnum, str, str]:
        membership = None
        prefix = None
        for i in range(len(MEMBERSHIP_PREFIXES)):
            for pref in MEMBERSHIP_PREFIXES[i]:
                if name.startswith(pref):
                    membership = ChannelMembership(i)
                    name = name.lstrip(pref)
                    prefix = pref
                    break
        if membership is None:
            membership = ChannelMembership.DEFAULT
            prefix = ''
        return membership, name, prefix
