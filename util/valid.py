import re
import time
from typing import Awaitable, Callable, Type

import aiohttp
import requests
from aiohttp import ClientResponse as AioResponse
from aiohttp import ClientSession
from al_utils.logger import Logger
from db.model import Anonymous, Protocol, Proxy

from util.converter import to_aiohttp_proxy, to_req_proxies

logger = Logger(__file__).logger

SYNC_M_PREFIX = 'sync_'
ASYNC_M_PREFIX = 'async_'
SyncValidCallable = Callable[[Proxy, float], Anonymous]
"""
All sync valid methods should be this type and startswith `sync_`.
Such as `sync_nmtsoft`.

>>> def sync_*(proxy, timeout)->Anonymous:
        pass
"""
AsyncValidCallable = Callable[[Proxy, float], Awaitable[Anonymous]]
"""
All async valid methods should be this type and startswith `async_`.
Such as `async_nmtsoft`.

>>> async def async_*(proxy, timeout)->Anonymous:
        pass
"""


class BaseValidCallables:
    pass


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
    def sync_get(url: str, proxy: Proxy, timeout: float = None, get_content: Callable[[requests.Response], str] = None):
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
        match proxy.protocol:
            case Protocol.HTTP:
                methods, _ = self.get_valid_methods(ValidHTTP)
            case Protocol.HTTPS:
                methods, _ = self.get_valid_methods(ValidHTTPS)
            case _:
                raise ValueError(f'Unsupport protocol {proxy.protocol}. '
                                 f'SOCKS are not supported in current version.')
        for method in methods:
            try:
                time_start = time.time()
                anon = method(proxy, timeout)
                time_req = time.time()-time_start
                return time_req, anon
            except (requests.exceptions.ProxyError,
                    requests.exceptions.SSLError):
                logger.warning(
                    f'Proxy refused to {method} via {proxy}.', exc_info=True)
                return -2, Anonymous.TRANSPARENT
            except (requests.exceptions.RequestException):
                logger.warning(
                    f'Cannot connect to {method} via {proxy}.', exc_info=True)
                continue
            except:
                logger.warning(
                    f'Occured err when {method} via {proxy}', exc_info=True)
                continue
        return -1, Anonymous.TRANSPARENT

    async def async_valid(self, proxy: Proxy, timeout: float = None) -> tuple[float, Anonymous]:
        """
        Asynchronous send a request to check speed and anonymous.

        NOTE
        -------------------
        Asynchronous is nonpreemptive. Speed is inaccurate(longer than sync).
        """
        timeout = timeout or self.timeout
        match proxy.protocol:
            case Protocol.HTTP:
                _, methods = self.get_valid_methods(ValidHTTP)
            case Protocol.HTTPS:
                _, methods = self.get_valid_methods(ValidHTTPS)
            case _:
                raise ValueError(f'Unsupport protocol {proxy.protocol}. '
                                 f'SOCKS are not supported in current version.')
        for method in methods:
            try:
                time_start = time.time()
                anon = await method(proxy, timeout)
                time_req = time.time()-time_start
                return time_req, anon
            except (aiohttp.ClientSSLError,
                    aiohttp.ClientConnectorError, # ClientProxyConnectionError
                    aiohttp.ClientHttpProxyError):
                logger.warning(
                    f'Proxy refused to {method} via {proxy}.', exc_info=True)
                return -2, Anonymous.TRANSPARENT
            except (aiohttp.ClientError):
                logger.warning(
                    f'Cannot connect to {method} via {proxy}.', exc_info=True)
                continue
            except:
                logger.warning(
                    f'Occured err when {method} via {proxy}', exc_info=True)
                continue
        return -1, Anonymous.TRANSPARENT

    def get_valid_methods(self, t: Type[BaseValidCallables]) -> tuple[list[SyncValidCallable], list[AsyncValidCallable]]:
        """
        Get methods from :param:`t` which startswith `SYNC_M_PREFIX` and `ASYNC_M_PREFIX`.

        :param t: Class which contain valid methods.
        :return: (sync_methods, async_methods)
        """
        methods = dir(t)
        syncs = []
        asyncs = []
        for m in methods:
            method = getattr(t, m)
            if hasattr(method, '__call__'):
                if m.startswith(SYNC_M_PREFIX):
                    syncs.append(method)
                if m.startswith(ASYNC_M_PREFIX):
                    asyncs.append(method)
        return syncs, asyncs

    def sync_http(self, proxy: Proxy, method: str, timeout: int = None) -> Anonymous:
        f = getattr(ValidHTTP, f'sync_{method}')
        logger.debug(f'Use {f}')
        return f(proxy, timeout)

    async def async_http(self, proxy: Proxy, method: str, timeout: float = None) -> Anonymous:
        f = getattr(ValidHTTP, f'async_{method}')
        logger.debug(f'Use {f}')
        return await f(proxy, timeout)

    def sync_https(self, proxy: Proxy, method: str, timeout: int = None) -> Anonymous:
        f = getattr(ValidHTTPS, f'sync_{method}')
        logger.debug(f'Use {f}')
        return f(proxy, timeout)

    async def async_https(self, proxy: Proxy, method: str, timeout: float = None) -> Anonymous:
        f = getattr(ValidHTTPS, f'async_{method}')
        logger.debug(f'Use {f}')
        return await f(proxy, timeout)


class ValidHTTP(BaseValidCallables):
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


class ValidHTTPS(BaseValidCallables):
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
