from db.model import Anonymous, Protocol, Proxy


def get_one_proxy(protocol: Protocol = Protocol.HTTPS, anonymous: Anonymous = Anonymous.HIGH, check_count: int = 20) -> Proxy:
    """
    Get a proxy.

    :param check_count: Valid :param:`check_count` times to get a usable proxy.
    :return: Proxy if found. After :param:`check_count` times doesn't get a usable proxy, return None.
    """
    # TODO: get one proxy from proxy service
    proxy = None
    if not proxy:
        return None
    return proxy
