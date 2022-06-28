import asyncio
import random
import re
from typing import Literal

from aiohttp import ClientSession
from al_utils.logger import Logger
from bs4 import BeautifulSoup, ResultSet, Tag
from db.model import Anonymous, Protocol, Proxy, Verify
from util.converter import to_aiohttp_proxy

from crawls.helper import get_one_proxy

logger = Logger(__file__).logger

CRAWL_RET = tuple[list[Proxy], list[str], list[str]]
"""
Return type for crawlers.

(proxies, successed urls, failed urls)
"""


async def kuaidaili(page_start: int = 1, page_end: int = 1, headers={}, timeout: int = 10, types: list[Literal['inha', 'intr']] = ['inha', 'intr'], **kwargs) -> CRAWL_RET:
    """
    快代理 https://www.kuaidaili.com

    :param page_start: From the start page number[include]. Default to `1`.
    :param page_end: To the end of the page number[include]. Default to `1`.
    :param headers: Optional request header. Such User-Agent, Cookies, Referer... Defaults to `{}`.
    :param timeout: Maximum timeout seconds. Defaults to `10`.
    :param types: List of anonymous types to crawl. Defaults to `['inha', 'intr']`

                    - inha: high
                    - intr: transparent

    :return: (proxies, successed urls, failed urls)
    """
    urls: list[tuple[str, Anonymous]] = []
    for t in types:
        match t:
            case 'inha':
                urls.append(
                    ('https://www.kuaidaili.com/free/inha/', Anonymous.HIGH))
            case 'intr':
                urls.append(
                    ('https://www.kuaidaili.com/free/intr/', Anonymous.TRANSPARENT))
            case _:
                continue
    proxies: list[Proxy] = []
    succs: list[str] = []
    fails: list[str] = []
    _p = to_aiohttp_proxy(await get_one_proxy(Protocol.HTTPS))
    async with ClientSession() as session:
        for baseurl, anonymous in urls:
            for page in range(page_start, page_end + 1):
                url = f'{baseurl}{page}/'
                try:
                    async with session.get(url=url, headers=headers, timeout=timeout, proxy=_p, **kwargs) as resp:
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
                            except:
                                logger.error(
                                    f"Cannot convert {result} when get {url}.", exc_info=True)
                                continue
                            else:
                                proxy = Proxy(
                                    protocol, ip, port, verify, anonymous, True, address)
                                proxies.append(proxy)
                except:
                    fails.append(url)
                    logger.error(
                        f"Occured errors when get {url}", exc_info=True)
                else:
                    succs.append(url)
                await asyncio.sleep(random.uniform(1.5, 5.0))  # sleep
    return proxies, succs, fails


async def nimadaili(page_start: int = 1, page_end: int = 1, headers={}, timeout: int = 10, types: list[Literal['putong', 'gaoni', 'http', 'https']] = ['putong', 'gaoni', 'http', 'https'], **kwargs) -> CRAWL_RET:
    """
    泥马代理 http://www.nimadaili.com

    :param page_start: From the start page number[include]. Default to `1`.
    :param page_end: To the end of the page number[include]. Default to `1`.
    :param headers: Optional request header. Such User-Agent, Cookies, Referer... Defaults to `{}`.
    :param timeout: Maximum timeout seconds. Defaults to `10`
    :param types: List of anonymous and protocol types to crawl. Defaults to `['putong', 'gaoni', 'http', 'https']`.

                    - putong: transparent
                    - gaoni: high
                    - http: HTTP
                    - https: HTTPS

    :return: (proxies, successed urls, failed urls)
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

    urls: list[str] = []
    for t in types:
        if t in ['putong', 'gaoni', 'http', 'https']:
            urls.append(f'http://www.nimadaili.com/{t}')
    proxies: list[Proxy] = []
    succs: list[str] = []
    fails: list[str] = []
    _p = to_aiohttp_proxy(await get_one_proxy(Protocol.HTTP))
    async with ClientSession() as session:
        for baseurl in urls:
            for page in range(page_start, page_end + 1):
                url = f'{baseurl}/{page}/'
                try:
                    async with session.get(url, headers=headers, timeout=timeout, proxy=_p, **kwargs) as resp:
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
                            except:
                                logger.error(
                                    f'Cannot convert {result} when get {url}.', exc_info=True)
                            else:
                                proxies.extend(ps)
                except:
                    fails.append(url)
                    logger.error(
                        f"Occured errors when get {url}.", exc_info=True)
                else:
                    succs.append(url)
                asyncio.sleep(random.uniform(1.5, 5.0))  # sleep
    return proxies, succs, fails


async def proxy_ip3366(page_start: int = 1, page_end: int = 1, headers={}, timeout: int = 10, **kwargs) -> CRAWL_RET:
    """
    齐云代理 https://proxy.ip3366.net

    :param page_start: From the start page number[include]. Default to `1`.
    :param page_end: To the end of the page number[include]. Default to `1`.
    :param headers: Optional request header. Such User-Agent, Cookies, Referer... Defaults to `{}`.
    :param timeout: Maximum timeout seconds. Defaults to `10`.
    :return: (proxies, successed urls, failed urls)
    """
    proxies: list[Proxy] = []
    succs: list[str] = []
    fails: list[str] = []
    _p = to_aiohttp_proxy(await get_one_proxy(Protocol.HTTPS))
    url = "https://proxy.ip3366.net/free/"
    async with ClientSession() as session:
        for page in range(page_start, page_end+1):
            params = {
                "action": "china",  # `action` only support `china`
                "page": page
            }
            try:
                async with session.get(url=url, headers=headers, params=params, timeout=timeout, proxy=_p, **kwargs) as resp:
                    if resp.status != 200:
                        raise ConnectionError(f'Cannot get {url}, '
                                              f'got status {resp.status}.')
                    html = await resp.text()
                    results: list[list[str]] = re.findall(
                        '<td data-title="IP">(.*?)</td>.*?'
                        '<td data-title="PORT">(.*?)</td>.*?'
                        '<td data-title="匿名度">(.*?)</td>.*?'
                        '<td data-title="类型">(.*?)</td>.*?'
                        '<td data-title="位置">(.*?)</td>',
                        html, re.S)
                    for result in results:
                        try:
                            ip = result[0].strip()
                            port = int(result[1].strip())
                            anonymous = Anonymous.HIGH if result[2].strip(
                            ).startswith('高') else Anonymous.TRANSPARENT
                            protocol = Protocol[result[3].strip()]
                            verify = Verify[result[3].strip()]
                            address = result[4].strip()
                        except:
                            logger.error(
                                f"Cannot convert {result} when get {url}.", exc_info=True)
                            continue
                        else:
                            proxy = Proxy(
                                protocol, ip, port, verify, anonymous, True, address)
                            proxies.append(proxy)

            except:
                fails.append(url)
                logger.error(
                    f"Occured errors when get {url}", exc_info=True)
            else:
                succs.append(url)
            await asyncio.sleep(random.uniform(1.5, 5.0))
    return proxies, succs, fails


async def ip3366(page_start: int = 1, page_end: int = 1, headers={}, timeout: int = 10, types: list[Literal['1', '2']] = ['1', '2'], **kwargs) -> CRAWL_RET:
    """
    云代理 http://www.ip3366.net

    :param page_start: From the start page number[include]. Default to `1`.
    :param page_end: To the end of the page number[include]. Default to `1`.
    :param headers: Optional request header. Such User-Agent, Cookies, Referer... Defaults to `{}`.
    :param timeout: Maximum timeout seconds. Defaults to `10`.
    :param types: List of anonymous types to crawl. Defaults to `['1', '2']`

                    - '1': high
                    - '2': anonymous or transparent

    :return: (proxies, successed urls, failed urls)
    """
    proxies: list[Proxy] = []
    succs: list[str] = []
    fails: list[str] = []
    _p = to_aiohttp_proxy(await get_one_proxy(Protocol.HTTP))
    baseurl = "http://www.ip3366.net/free"
    async with ClientSession() as session:
        for t in types:
            for page in range(page_start, page_end+1):
                params = {
                    "stype": types,
                    "page": page
                }
                url = baseurl
                try:
                    async with session.get(url=url, headers=headers, params=params, timeout=timeout, proxy=_p, **kwargs) as resp:
                        if resp.status != 200:
                            raise ConnectionError(f'Cannot get {url}, '
                                                  f'got status {resp.status}.')
                        html = await resp.text('gbk')
                        tbody = re.findall(r'<tbody>(.*?)</tbody>', html, re.S)
                        results: list[list[str]] = re.findall(
                            '<tr>.*?'
                            '<td>(.*?)''</td>.*?'  # ip
                            '<td>(.*?)</td>.*?'  # port
                            '<td>(.*?)</td>.*?'  # anon
                            '<td>(.*?)</td>.*?'  # proto
                            '<td>(.*?)</td>.*?'  # addr
                            '</tr>',
                            tbody[0], re.S)
                        for result in results:
                            try:
                                ip = result[0].strip()
                                port = int(result[1].strip())
                                anon = result[2].strip()
                                if anon.startswith('高'):
                                    anonymous = Anonymous.HIGH
                                elif anon.startswith('普'):
                                    anonymous = Anonymous.ANONYMOUS
                                else:
                                    anonymous = Anonymous.TRANSPARENT
                                protocol = Protocol[result[3].strip()]
                                address = result[4].strip()
                                verify = Verify[result[3].strip()]
                            except:
                                logger.error(
                                    f"Cannot convert {result} when get {url}.", exc_info=True)
                                continue
                            else:
                                proxy = Proxy(
                                    protocol, ip, port, verify, anonymous, True, address)
                                proxies.append(proxy)
                except:
                    fails.append(url)
                    logger.error(
                        f"Occured errors when get {url}", exc_info=True)
                else:
                    succs.append(url)
                await asyncio.sleep(random.uniform(1.5, 5.0))
    return proxies, succs, fails


async def ihuan(page_end: int = 1, headers={}, timeout: int = 10, **kwargs) -> CRAWL_RET:
    """
    小幻代理 https://ip.ihuan.me

    :param page_end: To the end of the page number[include]. Default to `1`.
    :param headers: Optional request header. Such User-Agent, Cookies, Referer... Defaults to `{}`.
    :param timeout: Maximum timeout seconds. Defaults to `10`.
    :return: (proxies, successed urls, failed urls)
    """
    proxies: list[Proxy] = []
    succs: list[str] = []
    fails: list[str] = []
    _p = to_aiohttp_proxy(await get_one_proxy(Protocol.HTTPS))
    baseurl = "https://ip.ihuan.me/"
    async with ClientSession() as session:
        page = 1
        for _ in range(1, page_end+1):
            params = {
                "page": page
            }
            url = baseurl
            try:
                async with session.get(url=baseurl, params=params, headers=headers, proxy=_p, timeout=timeout, **kwargs) as resp:
                    if resp.status != 200:
                        raise ConnectionError(f'Cannot get {url}, '
                                              f'got status {resp.status}.')
                    html = await resp.text()
                    soup = BeautifulSoup(html)
                    # region next page id
                    ul_result = re.findall(
                        r'<ul class="pagination">(.*?)</ul>', html, re.S)
                    li_result = re.findall(
                        r'<li>(.*?)</li>', ul_result[0], re.S)
                    next = re.findall(r'<.*page=(.*?)"', li_result[-1], re.S)
                    page = next[0]
                    # endregion
                    trs: ResultSet[Tag] = soup.table.tbody.find_all('tr')
                    for tr in trs:  # 单条数据
                        tds: ResultSet[Tag] = tr.find_all('td')
                        result = [t.text.strip() for t in tds]
                        try:
                            ip = result[0]
                            port = int(result[1])
                            address = result[2]
                            match result[4]:
                                case '支持':
                                    protocol = Protocol.HTTPS
                                    verify = Verify.HTTPS
                                case _:
                                    protocol = Protocol.HTTP
                                    verify = Verify.HTTP
                            match result[6]:
                                case '高匿':
                                    anonymous = Anonymous.HIGH
                                case '普匿':
                                    anonymous = Anonymous.ANONYMOUS
                                case _:
                                    anonymous = Anonymous.TRANSPARENT
                            domestic = True if result[2].startswith(
                                '中国') else False
                        except:
                            logger.error(
                                f"Cannot convert {result} when get {url}.", exc_info=True)
                            continue
                        else:
                            proxy = Proxy(
                                protocol, ip, port, verify, anonymous, domestic, address)
                            proxies.append(proxy)
            except:
                fails.append(url)
                logger.error(
                    f"Occured errors when get {url}", exc_info=True)
            else:
                succs.append(url)
            await asyncio.sleep(random.uniform(1.5, 5.0))
    return proxies, succs, fails


async def ip89(page_start: int = 1, page_end: int = 1, headers={}, timeout: int = 10, **kwargs) -> CRAWL_RET:
    """89免费代理 https://www.89ip.cn

    :param page_start: From the start page number[include]. Default to `1`.
    :param page_end: To the end of the page number[include]. Default to `1`.
    :param headers: Optional request header. Such User-Agent, Cookies, Referer... Defaults to `{}`.
    :param timeout: Maximum timeout seconds. Defaults to `10`.
    :return: (proxies, successed urls, failed urls)
    """
    proxies: list[Proxy] = []
    succs: list[str] = []
    fails: list[str] = []
    _p = to_aiohttp_proxy(await get_one_proxy(Protocol.HTTP))
    baseurl = "https://www.89ip.cn/"
    async with ClientSession() as session:
        for page in range(page_start, page_end+1):
            url = f'{baseurl}index_{page}.html'
            try:
                async with session.get(url=url, headers=headers, proxy=_p, timeout=timeout, **kwargs) as resp:
                    if resp.status != 200:
                        raise ConnectionError(f'Cannot get {url}, '
                                              f'got status {resp.status}.')
                    html = await resp.text()
                    tbody = re.findall(
                        r'<tbody>(.*?)</tbody>', html, re.S)
                    results = re.findall(
                        '<tr>.*?'
                        '<td>(.*?)</td>.*?'
                        '<td>(.*?)</td>.*?'
                        '<td>(.*?)</td>.*?'
                        '</tr>',
                        tbody[0], re.S)
                    for result in results:
                        try:
                            ip = result[0].strip()
                            port = int(result[1].strip())
                            address = result[2].strip()
                        except:
                            logger.error(
                                f"Cannot convert {result} when get {url}.", exc_info=True)
                            continue
                        else:
                            proxy = Proxy(Protocol.HTTP, ip, port, Verify.HTTP,
                                          Anonymous.TRANSPARENT, True, address)
                            proxies.append(proxy)
            except:
                fails.append(url)
                logger.error(
                    f"Occured errors when get {url}", exc_info=True)
            else:
                succs.append(url)
            await asyncio.sleep(random.uniform(1.5, 5.0))
    return proxies, succs, fails


async def ip89_api(num: int = 60, port: int = None, exclude_port: int = None, address: str = '', exclude_addr: str = '', isp: str = '',
                   headers: dict = {}, timeout: int = 10, **kwargs) -> CRAWL_RET:
    """89免费代理-API http://www.89ip.cn/api.html

    :param num: The count number. Default to `60.
    :param port: Specified port. Default to unlimit.
    :param address: Specified address. Default to unlimit.
    :param isp: Specified ISP(Internet Service Provider). Default to unlimit.
    :param headers: Optional request header. Such User-Agent, Cookies, Referer... Defaults to `{}`.
    :param timeout: Maximum timeout seconds. Defaults to `10`.
    :return: (proxies, successed urls, failed urls)
    """
    baseurl = "https://www.89ip.cn/tqdl.html?"
    params = {
        "api": 1,
        "num": num,
        "port": port if port and port > 0 else '',
        "address": address or '',
        "isp": isp or '',
        "kill_address": exclude_addr or '',
        'kill_port': exclude_port or '',
    }
    proxies: list[Proxy] = []
    succs: list[str] = []
    fails: list[str] = []
    _p = to_aiohttp_proxy(await get_one_proxy(Protocol.HTTPS))
    url = baseurl
    async with ClientSession() as session:
        try:
            async with session.get(url=url, params=params, proxy=_p, headers=headers, timeout=timeout, **kwargs) as resp:
                if resp.status != 200:
                    raise ConnectionError(f'Cannot get {url}, '
                                          f'got status {resp.status}.')
                html = await resp.text()
                results = re.findall(
                    r'(\d+.\d+.\d+.\d+):(\d+)', html, re.S)
                for result in results:
                    try:
                        _ip = result[0].strip()
                        _port = result[1].strip()
                    except:
                        logger.error(
                            f"Cannot convert {result} when get {url}.", exc_info=True)
                        continue
                    else:
                        proxy = Proxy(Protocol.HTTP, _ip, _port, Verify.HTTP,
                                      Anonymous.TRANSPARENT, True, address)
                        proxies.append(proxy)
        except:
            fails.append(url)
            logger.error(
                f"Occured errors when get {url}", exc_info=True)
        else:
            succs.append(url)
        await asyncio.sleep(random.uniform(1.5, 5.0))
    return proxies, succs, fails
