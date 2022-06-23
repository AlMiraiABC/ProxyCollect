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
    if not proxy:
        return ''
    return f'{proxy.protocol.name.lower()}://{proxy.ip}:{proxy.port}'


def to_dict(proxy: Proxy):
    """
    Convert proxy to k-v dict.
    """
    if not proxy:
        return {}
    return {
        'protocol': proxy.protocol.name,
        'ip': proxy.ip,
        'port': proxy.port,
        'verify': proxy.verify.name,
        'anonymous': proxy.anonymous.name,
        'domestic': proxy.domestic,
        'address': proxy.address,
        'speed': proxy.speed
    }
