import sys
from getopt import GetoptError, getopt

from commands.crawl import main as crawl_main
from commands.valid import main as valid_main

HELP = """Proxy Collect 2.0 https://github.com/AlMiraiABC/ProxyCollect
ARG:
    c, crawl    Crawl proxies.
    v, valid    Valid proxies.
PARAM:
    -h, --help  Help."""


def help(c=0):
    """Print help message."""
    print(HELP)
    exit(c)


def main(argv: list[str]):
    try:
        opts, args = getopt(argv, "h", ["help"])
    except GetoptError:
        print('test.py -i <inputfile> -o <outputfile>')
        exit(1)
    for opt, _ in opts:
        if opt in ['-h', '--help']:
            help()
    if not args:
        help(1)
    match args[0]:
        case 'c' | 'crawl':
            crawl_main(args[1:])
        case 'v' | 'valid':
            valid_main(args[1:])
        case _:
            help(2)


if __name__ == '__main__':
    main(sys.argv[1:])
