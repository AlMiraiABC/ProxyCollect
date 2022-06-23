import asyncio
import json
import os
from enum import Enum
from getopt import GetoptError, getopt
import sys
from typing import Callable, Type

from al_utils.console import ColoredConsole
from al_utils.logger import Logger
from db.model import Anonymous, Protocol, Proxy, Verify
from prettytable import PrettyTable
from services.query_service import QueryService
from util.config import QueryConfig, ValidConfig
from util.config_util import ConfigUtil
from util.converter import to_dict, to_url
from util.ip import is_formed_ipv4
from util.valid import Valid


logger = Logger(__file__).logger
HELP = """PARAM:
-h, --help              Help.
-c, --config <file>     Configuration file path.
-s, --schema <protocol> Protocol type.
    --protocol              http, https, socks4, socks5.
-h, --host <ip>         IP v4 address.
    --ip
-p, --port <port>       Port[0-65535].
-v, --verify <verify>   Verify type.
                           http, https, tcp, udp
-a, --anon <anonymous>  Anonymous type.
    --anonymous             trans, transparent, anonymous, confuse, high
-d, --dome, --domestic  Whether in domestic.
-n, --num <number>      Result count. >0.
-k, --skip <number>     Skip offset. ≥0.
-q, --query <type>      Query type.
                            query, random, check, count
                            Default is `query`.
                            * random: Select random proxies,
                                `skip` is ignored.
                            * check: Select random and check availability when query.
                                `num` is check times.
                                `skip` is ignored.
                            * count: Get the count number of query.
                                `export` and `save` are ignored.
-o, --output <type>     Result output format.
                            table, json, url
                            Default is `table`.
-x, --export <file.ext> Save results.
                            ext should be .txt, .json, .csv
                            Not saved by default."""

HEADERS = ['protocol', 'ip', 'port', 'verify',
           'anonymous', 'domestic', 'address', 'speed']


def help(c=0):
    """Print help message then exit."""
    print(HELP)
    exit(c)


def to_enum(t: Type[Enum], v: str) -> Enum:
    try:
        return t[v.upper()]
    except:
        print(f'Unexpected {t.__name__.lower()} type {v}.')
        exit(1)


def to_int(v: str, tip: str = '', comp: Callable[[int], bool] = lambda _: True):
    try:
        i = int(v)
        if not comp(i):
            raise ValueError(tip)
        return i
    except:
        print(f"Unexpected number {v}. {tip}")
        exit(1)


def to_table(proxies: list[Proxy]):
    tb = PrettyTable()
    tb.field_names = ['row', *HEADERS]
    for index, p in enumerate(proxies):
        tb.add_row([index+1, *list(to_dict(p).values())])
    return tb


def save_to(proxies: list[Proxy], fn: str):
    with open(fn, 'w', encoding='utf-8') as f:
        match os.path.splitext(fn)[-1]:
            case '.txt':
                f.writelines([to_url(p)+'\n' for p in proxies])
            case '.json':
                json.dump([to_dict(p) for p in proxies], f)
            case '.csv':
                import csv
                csvf = csv.DictWriter(f, HEADERS)
                csvf.writeheader()
                csvf.writerows([to_dict(p) for p in proxies])
            case _:
                raise ValueError(f'Unsupported file extension {fn}.')


class QueryType(Enum):
    QUERY = 1,
    RANDOM = 2,
    CHECK = 3,
    COUNT = 4


class OutputType(Enum):
    TABLE = 1,
    JSON = 2,
    URL = 3


def main(argv: list):
    try:
        opts, _ = getopt(argv, "hc:s:h:p:v:a:d:n:k:q:o:x:",
                         [
                             "help", "dome", "domestic",
                             "config=",
                             "protocol=", "schema=",
                             "ip=",
                             "port=",
                             "verify=",
                             "anon=", "anonymous=",
                             "num=",
                             "skip=",
                             "query=",
                             "output=",
                             "export="
                         ])
    except GetoptError:
        help(1)
    cf = 'config.json'
    protocol: Protocol = None
    ip: str = None
    port: int = None
    verify: Verify = None
    anonymous: Anonymous = None
    domestic: bool = None
    num: int = 1
    skip: int = 0
    query: QueryType = QueryType.QUERY
    output: OutputType = OutputType.TABLE
    export: str = None  # path
    for opt, arg in opts:
        match opt:
            case '-h' | '--help':
                help()
            case '-c' | '--config':
                cf = arg
            case '-s' | '--schema' | '--protocol':
                protocol = to_enum(Protocol, arg)
            case '-h' | '--ip' | '--host':
                if not is_formed_ipv4(arg):
                    print(f"Malformed ipv4 address {arg}.")
                    help(1)
                ip = arg
            case '-p' | '--port':
                port = to_int(arg, 'Port must be 0<=port<=65535.',
                              lambda x: 0 <= x <= 65535)
            case '-v' | '--verify':
                verify = to_enum(Verify, arg)
            case '-a' | '--anon' | '--anonymous':
                anonymous = to_enum(Anonymous, arg)
            case '-d' | '--dome' | '--domestic':
                domestic = True
            case '-n' | '--num':
                num = to_int(arg, 'Num must >0.', lambda x: x > 0)
            case '-k' | '--skip':
                skip = to_int(arg, 'Skip must >0.', lambda x: x > 0)
            case '-q' | '--query':
                query = to_enum(QueryType, arg)
            case '-o' | '--output':
                output = to_enum(OutputType, arg)
            case '-x' | '--export':
                if os.path.splitext(arg)[-1] not in ['.txt', '.csv', '.json']:
                    print(f'Unsupported saved file extension {export}.')
                    exit(1)
                export = arg
    ConfigUtil(cf)
    valid = Valid(ValidConfig.PUBLIC_IP, ValidConfig.TIMEOUT)
    service = QueryService(valid, QueryConfig.MAX_LIMIT, QueryConfig.BACKFILL)
    proxies: list[Proxy] = []
    # region query
    ColoredConsole.info('Starting query...')
    match query:
        case QueryType.COUNT:
            c = asyncio.run(service.get_count(protocol, ip, port, verify,
                                              anonymous, domestic))
            ColoredConsole.print(f'COUNT: {c}.')
            return
        case QueryType.CHECK:
            if num < 20:
                num = 20
                logger.debug(f'set num to {num}.')
                ColoredConsole.debug(f'Set num to {num}.')
            proxies = [asyncio.run(service.get_check(protocol, ip, port, verify,
                                                     anonymous, domestic, num))]
        case QueryType.RANDOM:
            proxies = asyncio.run(service.get_random(protocol, ip, port, verify,
                                                     anonymous, domestic, num))
        case _:
            proxies = asyncio.run(service.get(protocol, ip, port, verify,
                                              anonymous, domestic, num, skip))
    ColoredConsole.success(
        f"Got {len(proxies)} {'proxies' if len(proxies)>1 else 'proxy'}.")
    # endregion
    match output:
        case OutputType.JSON:
            ColoredConsole.print(json.dumps(
                [to_dict(p) for p in proxies], indent=2))
        case OutputType.URL:
            for p in proxies:
                ColoredConsole.print(to_url(p))
        case _:
            ColoredConsole.print(to_table(proxies).get_string())
    if export:
        save_to(proxies, export)
        ColoredConsole.success(f'Saved to {export}.')


if __name__ == '__main__':
    main(sys.argv[1:])
