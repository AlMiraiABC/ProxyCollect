from enum import Flag, unique

from util.ip_util import IpUtil


@unique
class Protocol(Flag):
    """Protocol types."""
    HTTP = 1 << 0,
    HTTPS = 1 << 1,
    SOCKS4 = 1 << 2,
    SOCKS5 = 1 << 3,


@unique
class Verify(Flag):
    """Proxy verify types."""
    HTTP = 1 << 0,
    HTTPS = 1 << 1,
    TCP = 1 << 2,
    UDP = 1 << 3,


class Proxy:
    def __init__(self, protocol: Protocol, ip: str, port: int, verify: Verify):
        self._protocol = protocol
        if not IpUtil.is_formed_ipv4(ip):
            raise ValueError("Invalid ip format")
        self._ip = ip
        if not port or port < 1 or port > 65535:
            raise ValueError("Invalid port, must be between 1 and 65535")
        self._port = port
        self._verify = verify

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

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, Proxy):
            return False
        if self.protocol == __o.protocol and \
                self.ip.string() == __o.ip.strip() and \
                self.port == __o.port and \
                self.verify == __o.verify:
            return True
        return False

    def __hash__(self) -> int:
        return hash(self.protocol.name+self.ip+self.port+self.verify.name)
