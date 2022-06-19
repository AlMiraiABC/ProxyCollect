"""
NOTE: Protocol must be lowercase
"""
import re
import time

import requests
from aiohttp import ClientSession
from al_utils.logger import Logger
from db.model import Anonymous, Proxy

logger = Logger(__file__).logger


class Valid:
    """Utils to check proxies availability."""

    def __init__(self, public_ip: str, timeout: float):
        self.public_ip = public_ip
        self.timeout = timeout

    def _check_anonymous(self, proxy: Proxy, content: str) -> Anonymous:
        """Check anonymous type. Whether real ip or proxy ip in :param:`content`"""
        if re.search(self.public_ip, content.text):
            return Anonymous.TRANSPARENT
        if re.search(proxy.ip, content.text):
            return Anonymous.ANONYMOUS
        return Anonymous.HIGH

    def req(self, proxy: Proxy, timeout: int = None):
        """
        Send request to check speed and anonymous.

        :param public_ip: Public ip address of your host.
        :param proxy: Proxy to verify.
        :param timeout: timeout
        :return: (speed, anonymous type). Or (-1, Transparent) if timeout or raise errors.
        """
        timeout = timeout or self.timeout
        time_start = time.time()
        try:
            anon = self.req_ifconfig(proxy, timeout)
        except Exception as ex:
            logger.warning(f'Raise {ex} when send request to ifconfig.')
            return -1, Anonymous.TRANSPARENT
        else:
            time_req = time.time()-time_start
            return time_req, anon

    # region req
    def req_ifconfig(self, proxy: Proxy, timeout: float = None):
        """
        Check ip anonymous type using ifconfig.

        :raise: ConnectionError if response status code is not 200.
        """
        url = 'https://ifconfig.me/forwarded'
        proxies = {proxy.protocol.name.lower(): f"{proxy.ip}:{proxy.port}"}
        timeout = timeout or self.timeout
        content = requests.get(url=url, timeout=timeout, proxies=proxies)
        if content.status_code == 200:
            return self._check_anonymous(proxy, content.text)
        raise ConnectionError(f"Excepted response code 200, "
                              f"but got {content.status_code}.")
    # endregion

    async def async_req(self, proxy: Proxy, timeout: float = None, session: ClientSession = None):
        """
        Asynchronous send a request to check speed and anonymous.

        NOTE
        -------------------
        * Asynchronous is nonpreemptive. Speed is inaccurate(longer than sync).
        """
        timeout = timeout or self.timeout
        time_start = time.time()
        try:
            anon = await self.async_req_ifconfig(proxy, timeout, session)
        except Exception:
            return -1, Anonymous.TRANSPARENT
        else:
            time_req = time.time()-time_start
            return time_req, anon

    # region async req
    async def async_req_ifconfig(self, proxy: Proxy, timeout: float = None, session: ClientSession = None):
        url = 'https://ifconfig.me/forwarded'
        proxy = f"{proxy.protocol.name.lower()}://{proxy.ip}:{proxy.port}"
        timeout = timeout or self.timeout

        async def get(s: ClientSession):
            async with s.get(url, proxy=proxy, timeout=timeout) as resp:
                if resp.status == 200:
                    return self._check_anonymous(proxy, await resp.text())
                raise ConnectionError(f"Excepted response code 200, "
                                      f"but got {resp.status}.")
        if session:
            return await get(session)
        async with ClientSession() as session:
            return await get(session)
    # endregion
