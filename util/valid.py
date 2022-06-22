import re
import time
from typing import Awaitable, Callable, Literal

import requests
from aiohttp import ClientResponse as AioResponse, ClientSession
from al_utils.logger import Logger
from db.model import Anonymous, Protocol, Proxy
from requests import Response

from util.converter import to_aiohttp_proxy, to_req_proxies

logger = Logger(__file__).logger


class ValidHelper:
    DEFAULT_TIMEOUT = 10
    PUBLIC_IP: str = ''

    @staticmethod
    def check_anonymous(proxy: Proxy, content: str) -> Anonymous:
        """Check anonymous type. Whether :param:`public_ip` or `proxy.ip` in :param:`content`"""
        if re.search(ValidHelper.PUBLIC_IP, content):
            return Anonymous.TRANSPARENT
        if re.search(proxy.ip, content):
            return Anonymous.ANONYMOUS
        return Anonymous.HIGH

    @staticmethod
    def sync_get(url: str, proxy: Proxy, timeout: float = None, get_content: Callable[[Response], str] = None):
        """
        Send request via GET to :param:`url` to check :param:`proxy`'s anonymous type synchronously.

        :param url: Dist url send to.
        :param proxy: Used proxy.
        :param timeout: Timeout seconds.
        :param get_content: Callback to get responsed content text which contain IPs to check anonymous.

        :raise: ConnectionError if response status code is not 200.
        """
        timeout = timeout or ValidHelper.DEFAULT_TIMEOUT
        get_content = get_content or (lambda x: x.text)
        response = requests.get(url=url, timeout=timeout,
                                proxies=to_req_proxies(proxy))
        if response.status_code == 200:
            logger.debug(response.text)
            return ValidHelper.check_anonymous(proxy, get_content(response))
        raise ConnectionError(f"Excepted response code 200, "
                              f"but got {response.status_code}"
                              f"<{response.reason}>")

    @staticmethod
    async def async_get(url: str, proxy: Proxy, timeout: float = None, get_content: Callable[[AioResponse], Awaitable[str]] = None):
        """
        Send request via GET to :param:`url` to check :param:`proxy`'s anonymous type synchronously.

        :raise: ConnectionError if response status code is not 200.

        See also:
        ---------------------
        :meth:`ValidHelper.sync_get`
        """
        timeout = timeout or ValidHelper.DEFAULT_TIMEOUT

        async def get_content(resp: AioResponse):
            return await resp.text()

        async with ClientSession() as session:
            async with session.get(url, timeout=timeout, proxy=to_aiohttp_proxy(proxy)) as resp:
                if resp.status == 200:
                    return ValidHelper.check_anonymous(proxy, await get_content(resp))
                raise ConnectionError(f"Excepted response code 200, "
                                      f"but got {resp.status}."
                                      f"<{resp.reason}>")


class Valid:
    """Utils to check proxies availability."""

    def __init__(self, public_ip: str, timeout: float):
        self.public_ip = public_ip
        self.timeout = timeout
        ValidHelper.PUBLIC_IP = public_ip

    def sync_valid(self, proxy: Proxy, timeout: int = None) -> tuple[float, Anonymous]:
        """
        Send request to check speed and anonymous.

        :param proxy: Proxy to verify.
        :param timeout: timeout
        :return: (speed, anonymous type). Or (-1, Transparent) if timeout or raise errors.
        :raise ValueError: Socks are not supported in current version.
        """
        timeout = timeout or self.timeout
        time_start = time.time()
        match proxy.protocol:
            case Protocol.HTTP:
                f = self.sync_http
            case Protocol.HTTPS:
                f = self.sync_https
            case _:
                raise ValueError(f'Unsupport protocol {proxy.protocol}. '
                                 f'SOCKS are not supported in current version.')
        try:
            anon = f(proxy, timeout)
            time_req = time.time()-time_start
            return time_req, anon
        except:
            logger.warning(f'Cannot get from {f}.', exc_info=True)
        return -1, Anonymous.TRANSPARENT

    async def async_valid(self, proxy: Proxy, timeout: float = None) -> tuple[float, Anonymous]:
        """
        Asynchronous send a request to check speed and anonymous.

        NOTE
        -------------------
        Asynchronous is nonpreemptive. Speed is inaccurate(longer than sync).
        """
        timeout = timeout or self.timeout
        time_start = time.time()
        match proxy.protocol:
            case Protocol.HTTP:
                f = self.async_http
            case Protocol.HTTPS:
                f = self.async_https
            case _:
                raise ValueError(
                    f'Unsupport protocol {proxy.protocol}. SOCKS are not supported in current version.')
        try:
            anon = await f(proxy, timeout)
            time_req = time.time()-time_start
            return time_req, anon
        except:
            logger.warning(f'Cannot get from {f}.', exc_info=True)
        return -1, Anonymous.TRANSPARENT

    def sync_http(self, proxy: Proxy, timeout: int = None, method: Literal['nmtsoft'] = 'nmtsoft') -> Anonymous:
        f = getattr(ValidHTTP, f'sync_{method}')
        logger.debug(f'Use {f}')
        return f(proxy, timeout)

    async def async_http(self, proxy: Proxy, timeout: float = None, method: Literal['nmtsoft'] = 'nmtsoft') -> Anonymous:
        f = getattr(ValidHTTP, f'async_{method}')
        logger.debug(f'Use {f}')
        return await f(proxy, timeout)

    def sync_https(self, proxy: Proxy, timeout: int = None, method: Literal['nmtsoft', 'ifconfig'] = 'ifconfig') -> Anonymous:
        f = getattr(ValidHTTPS, f'sync_{method}')
        logger.debug(f'Use {f}')
        return f(proxy, timeout)

    async def async_https(self, proxy: Proxy, timeout: float = None, method: Literal['nmtsoft', 'ifconfig'] = 'ifconfig') -> Anonymous:
        f = getattr(ValidHTTPS, f'async_{method}')
        logger.debug(f'Use {f}')
        return await f(proxy, timeout)


class ValidHTTP:
    @staticmethod
    def sync_nmtsoft(proxy: Proxy, timeout: float = None):
        url = 'http://checkip.nmtsoft.net/forwarded'
        return ValidHelper.sync_get(url, proxy, timeout, lambda x: x.text)

    @staticmethod
    async def async_nmtsoft(proxy: Proxy, timeout: float = None):
        async def get_content(resp: AioResponse):
            return await resp.text()
        url = 'http://checkip.nmtsoft.net/forwarded'
        return await ValidHelper.async_get(url, proxy, timeout, get_content)


class ValidHTTPS:
    @staticmethod
    def sync_ifconfig(proxy: Proxy, timeout: float = None):
        url = 'https://ifconfig.me/forwarded'
        return ValidHelper.sync_get(url, proxy, timeout, lambda x: x.text)

    @staticmethod
    async def async_ifconfig(proxy: Proxy, timeout: float = None):
        async def get_content(resp: AioResponse):
            return await resp.text()
        url = 'https://ifconfig.me/forwarded'
        return await ValidHelper.async_get(url, proxy, timeout, get_content)

    @staticmethod
    def sync_nmtsoft(proxy: Proxy, timeout: float = None):
        url = 'https://checkip.nmtsoft.net/forwarded'
        return ValidHelper.sync_get(url, proxy, timeout, lambda x: x.text)

    @staticmethod
    async def async_nmtsoft(proxy: Proxy, timeout: float = None):
        async def get_content(resp: AioResponse):
            return await resp.text()
        url = 'https://checkip.nmtsoft.net/forwarded'
        return await ValidHelper.async_get(url, proxy, timeout, get_content)


class ValidTCP:
    pass


class ValidUDP:
    pass
