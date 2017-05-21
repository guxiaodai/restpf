from enum import Enum, auto


class EnumByUpperCaseName(Enum):

    def _generate_next_value_(name, *args, **kwargs):
        return name.upper()


class EnumByLowerCaseName(Enum):

    def _generate_next_value_(name, *args, **kwargs):
        return name.lower()


class HTTPMethodConfig(EnumByUpperCaseName):

    POST = auto()
    GET = auto()
    PATCH = auto()
    DELETE = auto()
    PUT = auto()
    OPTIONS = auto()


class AppearanceConfig(EnumByUpperCaseName):

    REQUIRE = auto()
    PROHIBITE = auto()
    FREE = auto()


class UnknowAttributeConfig(EnumByUpperCaseName):

    IGNORE = auto()
    PROHIBITE = auto()


class CallbackRegistrarOptions(EnumByLowerCaseName):

    BEFORE_ALL = auto()
    RUN_AFTER = auto()


class TopologySearchColor(Enum):

    WHITE = auto()
    GRAY = auto()
    BLACK = auto()
