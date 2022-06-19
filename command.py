import sys
from getopt import GetoptError, getopt

from commands.crawl import main as crawl_main


def help():
    """Print help message."""
    print("""Proxy Collect 2.0 https://github.com/AlMiraiABC/ProxyCollect
ARG:
    c, crawl    Crawl proxies.
    v, valid    Valid proxies.
PARAM:
    -h, --help  Help.""")
    exit(0)


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
        help()
    match args[0]:
        case 'c' | 'crawl':
            crawl_main(args[1:])


if __name__ == '__main__':
    main(sys.argv[1:])
