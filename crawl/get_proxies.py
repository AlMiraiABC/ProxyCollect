import asyncio
import random
import re
from asyncio import Semaphore
from typing import Callable

from aiohttp import ClientSession
from al_utils.logger import Logger
from db.model import Anonymous, Protocol, Proxy, Verify

logger = Logger(__file__).logger

CRAW_RET = tuple[list[Proxy], list[str], list[str]]
"""
(proxies, successed urls, failed urls)
"""


class GetFreeProxy:
    """
    获得互联网上的公开代理

    Support
    -------------
    - 快代理 https://www.kuaidaili.com/
    - 泥马代理 http://www.nimadaili.com
    - 66免费代理网 http://www.66ip.cn/ http://www.66daili.cn/
    - 89免费代理 http://www.89ip.cn/
    - 云代理 http://www.ip3366.net/
    - 小幻HTTP代理 https://ip.ihuan.me/
    """

    @staticmethod
    def _get_one_proxy(protocol: Protocol = Protocol.HTTPS, anonymous: Anonymous = Anonymous.HIGH, check_count: int = 20,
                       cb: Callable[[Protocol, Anonymous, int], Proxy] = None) -> str:
        """
        Get a proxy string. <protocol://ip:port>

        :param check_count: Valid :param:`check_count` times to get a usable proxy.
        :param cb: Callback to get a proxy. `(protocol, anonymous, check_count) => proxy`
        :return: Proxy if found. After :param:`check_count` times doesn't get a usable proxy, return None.
        """
        cb = cb or (lambda *_: None)
        proxy = cb(protocol, anonymous, check_count)
        if not proxy:
            return ''
        return f'{proxy.protocol.name.lower()}://{proxy.ip}:{proxy.port}'

    @staticmethod
    async def kuaidaili(page_start: int = 1, page_end: int = 1, headers={}, timeout: int = 10, semaphore: int = 10) -> CRAW_RET:
        """
        快代理 https://www.kuaidaili.com

        :param page_start: 起始页
        :param page_end:终止页
            >>> range(page_start, page_end+1)
        """
        urls: list = [
            ('https://www.kuaidaili.com/free/inha/', Anonymous.HIGH),
            ('https://www.kuaidaili.com/free/intr/', Anonymous.TRANSPARENT)
        ]
        proxies: list[Proxy] = []
        succs: list[str] = []
        fails: list[str] = []
        async with ClientSession() as session:
            for baseurl, anonymous in urls:
                for page in range(page_start, page_end + 1):
                    url = f'{baseurl}{page}/'
                    proxy = GetFreeProxy._get_one_proxy(
                        protocol=Protocol.HTTPS, anonymous=Anonymous.HIGH)
                    async with Semaphore(semaphore):
                        try:
                            async with session.get(url=url, headers=headers, timeout=timeout, proxy=proxy) as resp:
                                if resp.status != 200:
                                    raise ConnectionError(f'Cannot get {url}, '
                                                          f'got status {resp.status}.')
                                html = await resp.text()
                                results = re.findall(
                                    'data-title="IP">(.*?)</td>.*?'
                                    'data-title="PORT">(.*?)</td>.*?'
                                    'data-title="类型">(.*?)</td>.*?'
                                    'data-title="位置">(.*?)</td>',
                                    html, re.S
                                )
                                for result in results:
                                    try:
                                        ip = result[0]
                                        protocol = Protocol[result[2]]
                                        verify = Verify[result[2]]
                                        address = result[3]
                                        port = int(result[1])
                                    except KeyError:
                                        logger.error(
                                            f"Cannot convert {result} when get {url}.")
                                    else:
                                        proxy = Proxy(
                                            protocol, ip, port, verify, anonymous, True, address)
                                        proxies.append(proxy)
                        except Exception as ex:
                            fails.append(url)
                            logger.error(
                                f"Occured errors when get {url}. {ex}")
                        else:
                            succs.append(url)
                        asyncio.sleep(random.uniform(1.5, 5.0))  # sleep
        return proxies, succs, fails

    @staticmethod
    async def nimadaili(page_start: int = 1, page_end: int = 1, headers={}, timeout: int = 10, semaphore: int = 10) -> CRAW_RET:
        """
        泥马代理 http://www.nimadaili.com

        :param page_start: 起始页
        :param page_end:终止页
            >>> range(page_start, page_end+1)
        """

        def to_proxy(info: tuple[str, str, str, str]) -> list[Proxy]:
            """
            Convert :param:`info` tuple to :class:`Proxy` list.

            :param info: (ip:port, protocol, anonymous, address)
            """
            ip, port = info[0].split(':')
            port = int(port)
            protocols = re.findall('([a-zA-Z]+)', info[1])
            anonymous = Anonymous.HIGH \
                if info[2].startswith('高') \
                else Anonymous.TRANSPARENT
            return [Proxy(Protocol[protocol], ip, port, Verify[protocol], anonymous, True, info[3]) for protocol in protocols]

        urls: list = [
            'http://www.nimadaili.com/putong/',  # 普通
            'http://www.nimadaili.com/gaoni/',  # 高匿
            'http://www.nimadaili.com/http/',  # http
            'http://www.nimadaili.com/https/'  # https
        ]
        proxies: list[Proxy] = []
        succs: list[str] = []
        fails: list[str] = []
        async with ClientSession() as session:
            for baseurl in urls:
                for page in range(page_start, page_end + 1):
                    url = f'{baseurl}{page}/'
                    proxy = GetFreeProxy._get_one_proxy(
                        protocol=Protocol.HTTP, anonymous=Anonymous.HIGH)
                    async with Semaphore(semaphore):
                        try:
                            async with session.get(url, headers=headers, proxy=proxy, timeout=timeout) as resp:
                                if resp.status != 200:
                                    raise ConnectionError(f'Cannot get {url}, '
                                                          f'got status {resp.status}.')
                                html = await resp.text()
                                results = re.findall(
                                    '<tr>.*?'
                                    '<td>(.*?)</td>.*?'
                                    '<td>(.*?)</td>.*?'
                                    '<td>(.*?)</td>.*?'
                                    '<td>(.*?)</td>.*?'
                                    '</tr>',
                                    html, re.S
                                )
                                for result in results:
                                    try:
                                        ps = to_proxy(result)
                                    except Exception as e:
                                        logger.error(
                                            f'Cannot convert {result} when get {url}. {e}')
                                    else:
                                        proxies.extend(ps)
                        except Exception as ex:
                            fails.append(url)
                            logger.error(
                                f"Occured errors when get {url}. {ex}")
                        else:
                            succs.append(url)
                        asyncio.sleep(random.uniform(1.5, 5.0))  # sleep
        return proxies, succs, fails
