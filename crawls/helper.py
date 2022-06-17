from db.model import Anonymous, Protocol


def get_one_proxy(protocol: Protocol = Protocol.HTTPS, anonymous: Anonymous = Anonymous.HIGH, check_count: int = 20) -> str:
    """
    Get a proxy string. <protocol://ip:port>

    :param check_count: Valid :param:`check_count` times to get a usable proxy.
    :return: Proxy string (`protocol://ip:port`) if found. After :param:`check_count` times doesn't get a usable proxy, return None.
    """
    # TODO: get one proxy from proxy service
    proxy = None
    if not proxy:
        return None
    return f'{proxy.protocol.name.lower()}://{proxy.ip}:{proxy.port}'
