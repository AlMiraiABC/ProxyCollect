from copy import copy
from enum import Enum, unique

from util.ip_util import IpUtil


@unique
class Protocol(Enum):
    """Protocol types."""
    HTTP = 1
    HTTPS = 2
    SOCKS4 = 3
    SOCKS5 = 4


@unique
class Verify(Enum):
    """Proxy verify types."""
    HTTP = 1
    HTTPS = 2
    TCP = 3
    UDP = 4


@unique
class Anonymous(Enum):
    """Anonymous types."""
    TRANSPARENT = 1
    ANONYMOUS = 2
    CONFUSE = 3
    HIGH = 4


class Proxy:
    def __init__(self, protocol: Protocol, ip: str, port: int, verify: Verify, anonymous: Anonymous,
                 domestic: bool = True, address: str = '', speed: float = 0):
        self._protocol = protocol
        if not IpUtil.is_formed_ipv4(ip):
            raise ValueError("Invalid ip format")
        self._ip = ip
        if not port or int(port) < 1 or int(port) > 65535:
            raise ValueError("Invalid port, must be between 1 and 65535")
        self._port = port
        self._verify = verify
        self._anonymous = anonymous
        # public properties
        self.domestic: bool = domestic or True
        self.address: str = address or ''
        self.speed: float = speed or 0

    @property
    def protocol(self):
        return self._protocol

    @property
    def ip(self):
        return self._ip

    @property
    def port(self):
        return self._port

    @property
    def verify(self):
        return self._verify

    @property
    def anonymous(self):
        return self._anonymous

    def __eq__(self, __o: object) -> bool:
        if __o is None:
            return False
        if id(self) == id(__o):
            return True
        if not isinstance(__o, self.__class__):
            return False
        if self.protocol == __o.protocol and \
                self.ip.strip() == __o.ip.strip() and \
                self.port == __o.port and \
                self.verify == __o.verify and \
                self.anonymous == __o.anonymous:
            return True
        return False

    def __hash__(self) -> int:
        return hash(self.protocol.name+self.ip+self.port+self.verify.name)

    def copy(self):
        return copy(self)


class StoredProxy(Proxy):
    """:class:`Proxy` which stored in, add `id` and `score` properties."""

    def __init__(self, id: str | int,  protocol: Protocol, ip: str, port: int, verify: Verify, score: int, anonymous: Anonymous,
                 domestic: bool = True, address: str = '', speed: float = 0):
        super(StoredProxy, self).__init__(
            protocol, ip, port, verify, anonymous, domestic, address, speed)
        self._id = id
        self._score = score

    @property
    def id(self):
        return self._id

    @property
    def score(self):
        return self._score
