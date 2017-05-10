from enum import Enum, auto


class EnumByName(Enum):

    def _generate_next_value_(name, *args, **kwargs):
        return name


class HTTPMethodConfig(EnumByName):

    POST = auto()
    GET = auto()
    PATCH = auto()
    DELETE = auto()
    PUT = auto()
    OPTIONS = auto()


class AppearanceConfig(EnumByName):

    REQUIRE = auto()
    PROHIBITE = auto()
    FREE = auto()


class UnknowAttributeConfig(EnumByName):

    IGNORE = auto()
    PROHIBITE = auto()
