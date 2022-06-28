from db.model import Anonymous, Protocol, Proxy
from services.query_service import QueryService
from util.config import ValidConfig
from util.valid import Valid

_service = QueryService(
    Valid(ValidConfig.PUBLIC_IP, ValidConfig.TIMEOUT), backfill=True)


async def get_one_proxy(protocol: Protocol = Protocol.HTTPS, anonymous: Anonymous = Anonymous.HIGH, check_count: int = 20) -> Proxy:
    """
    Get a proxy.

    :param check_count: Valid :param:`check_count` times to get a usable proxy.
    :return: Proxy if found. After :param:`check_count` times doesn't get a usable proxy, return None.
    """
    proxy = await _service.get_random(protocol, anonymous=anonymous, count=check_count)
    if not proxy:
        return None
    return proxy
