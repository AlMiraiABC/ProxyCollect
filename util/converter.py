from db.model import Protocol, Proxy


def to_aiohttp_proxy(proxy: Proxy) -> str | None:
    """
    Convert :param:`proxy` to aiohttp proxy.

    HTTPS will conver to HTTP(https is not support).

    Socks are not supported and raise :class:`ValueError`
    """
    if not proxy:
        return None
    protocol = proxy.protocol
    match proxy.protocol:
        case Protocol.HTTP | Protocol.HTTPS:
            protocol = 'http'
        case _:
            raise ValueError(f'Only support http and https, '
                             f'bug got {proxy.protocol}')
    return f'{protocol}://{proxy.ip}:{proxy.port}'


def to_req_proxies(proxy: Proxy):
    """
    Convert Proxy to requests proxies dict.
    """
    if not proxy:
        return None
    return {proxy.protocol.name.lower(): f'{proxy.ip}:{proxy.port}'}


def to_url(proxy: Proxy):
    """
    Convert Proxy to url.

    `<protocol>://<ip>:<port>`
    """
    return f'{proxy.protocol.name.lower()}://{proxy.ip}:{proxy.port}'
