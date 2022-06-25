import asyncio
import sys
from getopt import GetoptError, getopt

from al_utils.console import ColoredConsole
from al_utils.logger import Logger
from prettytable import PrettyTable
from services.valid_service import ValidService
from util.config import ValidConfig
from util.config_util import ConfigUtil
from util.ip import is_formed_ipv4
from util.valid import Valid

logger = Logger(__file__).logger


HELP = """PARAM:
-h, --help                  Print help message.
-s, --semaphore <semaphore> The maximum number of concurrent.
                            Default is 50.
-p, --patch <patch>         Number of each epoch to valid.
                            Default is 500."""


def help(c=0):
    """Print help message then exit."""
    print(HELP)
    exit(c)


def _cb(_, counts, fails, timeouts):
    """Callback of each epoch."""
    ColoredConsole.info(f'Valid {counts} proxies')
    if fails:
        ColoredConsole.error(f'Failed to valid {fails} proxies.')
    if timeouts:
        ColoredConsole.error(f'Timeout to valid {timeouts} proxies.')


def statistics(res: list):
    tb = PrettyTable()
    tb.field_names = ['row', 'count', 'success', 'fail', 'timeout']
    cc, cf, ct = 0, 0, 0
    for index, r in enumerate(res):
        tb.add_row([index+1, r[0], r[0]-r[1]-r[2], r[1], r[2]])
        cc += r[0]
        cf += r[1]
        ct += r[2]
    tb.add_row(['Total', cc, cc-cf-ct, cf, ct])
    tb.align = 'r'
    return tb


def main(argv: list[str]):
    sem = ValidConfig.SEMAPHORE
    patch = ValidConfig.PATCH
    cf = 'config.json'
    pubip: str = None
    timeout = ValidConfig.TIMEOUT
    try:
        opts, _ = getopt(argv, "hc:s:p:i:t:", [
                         "help",
                         "config=",
                         "semaphore=",
                         "patch=",
                         "pubip=",
                         "timeout="])
    except GetoptError:
        help(1)
    for opt, arg in opts:
        match opt:
            case '-h' | '--help':
                help()
            case '-s' | '--semaphore':
                sem = int(arg)
            case '-p' | '--patch':
                patch = int(arg)
            case '-c' | '--config':
                cf = arg
            case '-i' | '--pubip':
                if not is_formed_ipv4(arg):
                    print(f"Malformed public ip address {arg}.")
                pubip = arg
            case '-t' | '--timeout':
                timeout = int(arg)
    if timeout < 1:
        timeout = ValidConfig.TIMEOUT
    if not pubip:
        pubip = ValidConfig.PUBLIC_IP
    ConfigUtil(cf)
    service = ValidService(Valid(pubip, timeout), patch, sem)
    logger.info(f'Start valid with patch {patch} and semaphore {sem}.')
    ret = asyncio.run(service.run(_cb))
    logger.info(f'Valid finished.')
    print(statistics(ret))


if __name__ == '__main__':
    main(sys.argv[1:])
