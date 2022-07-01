from enum import Enum

from aiohttp.web import (Application, Request, Response, RouteTableDef,
                         json_response, run_app)
from commands.helper import to_enum, to_int
from db.model import Anonymous, Protocol, Proxy
from services.query_service import QueryService
from util.config import QueryConfig, ScoreConfig, ValidConfig
from util.converter import to_dict, to_url
from util.valid import Valid

routes = RouteTableDef()
_service = QueryService(Valid(ValidConfig.PUBLIC_IP,
                        ValidConfig.TIMEOUT), max_page_size=20, backfill=True)


class ProxyFormatType(Enum):
    DICT = 1
    JSON = 1
    URL = 2


def format_proxies(t: ProxyFormatType, proxies: list[Proxy]) -> Response:
    match t:
        case ProxyFormatType.DICT | ProxyFormatType.JSON:
            if not proxies:
                return json_response([])
            return json_response([to_dict(proxy) for proxy in proxies])
        case ProxyFormatType.URL:
            if not proxies:
                return Response(body='')
            return Response(body='\n'.join([to_url(proxy) for proxy in proxies]))
        case _:
            raise ValueError(f'Unsupported format type {t}.')


def format_base_req(req: dict[str, str]):
    protocol: Protocol | None = None
    anonymous: Anonymous | None = None
    t: ProxyFormatType | None = None
    for k, v in req.items():
        match k:
            case 'p' | 'protocol' | 'proto':
                protocol = to_enum(Protocol, v)
            case 'a' | 'anon' | 'anonymous':
                anonymous = to_enum(Anonymous, v)
            case 't' | 'type':
                t = to_enum(ProxyFormatType, v)
    return protocol, anonymous, t


@routes.get('/list')
async def index(request: Request):
    req = request.query
    protocol: Protocol = None
    anonymous: Anonymous = None
    page_size: int = QueryConfig.DEFAULT_PS
    page_num: int = 1
    protocol, anonymous, t = format_base_req(req)
    t: ProxyFormatType = t or ProxyFormatType.DICT
    for k, v in req.items():
        match k:
            case 's' | 'ps' | 'page_size':
                page_size = to_int(v)
                if page_size is None or page_size < 1:
                    page_size = QueryConfig.DEFAULT_PS
                if page_size > QueryConfig.MAX_PS:
                    page_size = QueryConfig.MAX_PS
            case 'n' | 'pn' | 'page_num':
                page_num = to_int(v)
                if page_num is None or page_num < 1:
                    page_num = 1
    limit = page_size
    skip = (page_num-1)*page_size
    proxies = await _service.get(protocol=protocol, anonymous=anonymous,
                                 min_score=ScoreConfig.INIT, limit=limit, skip=skip)
    return format_proxies(t, proxies)


@routes.get('/random')
async def random(request: Request):
    req = request.query
    protocol, anonymous, t = format_base_req(req)
    t: ProxyFormatType = t or ProxyFormatType.DICT
    proxies = await _service.get_random(protocol=protocol, anonymous=anonymous, min_score=ScoreConfig.INIT)
    return format_proxies(t, proxies)


@routes.get('/guarantee')
async def guarantee(request: Request):
    req: dict[str, any] = await request.json()
    protocol, anonymous, t = format_base_req(req)
    t: ProxyFormatType = t or ProxyFormatType.DICT
    proxy = await _service.get_check(protocol=protocol, anonymous=anonymous, min_score=ScoreConfig.INIT)
    return format_proxies(t, [proxy])

app = Application()
app.add_routes(routes)
if __name__ == '__main__':
    run_app(app)
