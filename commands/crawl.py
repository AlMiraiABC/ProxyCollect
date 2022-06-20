import asyncio
import sys
from getopt import GetoptError, getopt
from typing import Callable

from al_utils.console import ColoredConsole
from al_utils.logger import Logger
from prettytable import PrettyTable
from services.crawl_service import CrawlService
from util.config import CrawlsConfig, CrawlsCrawlerConfig
from util.config_util import ConfigUtil

logger = Logger(__file__).logger
service = CrawlService()


async def run(conf: list[CrawlsCrawlerConfig], sem: int = 10, cb: Callable[[dict], None] = None) -> list[dict]:
    """
    :return: [
        {
            'crawler': Config of crawler,
            'susurl': Request successed urls,
            'failurl': Request failed urls,
            'count': Total crawled proxies,
            'insert': Count of successfully inserted proxies,
            'exist': Count of exist proxies, skip to insert,
            'failed': Count of proxies failed to insert,
        }
    ]
    """
    ret: list[dict] = []
    sem = sem if sem and sem > 0 else 10
    for crawler in conf:
        logger.info(f'Start crawling {crawler}')
        if not crawler.get('callable'):
            logger.error(
                f"Crawler's config {crawler} must have `callable` key.")
            ColoredConsole.error(
                f"Crawler's config {crawler} must have `callable` key. Skip it.")
            continue
        try:
            async with asyncio.Semaphore(sem):
                proxies, sus, fus = await service.run(crawler['callable'], *crawler.get('args', ()), **crawler.get('kwargs', {}))
        except:
            logger.error(f'Crawl {crawler} failed.', exc_info=True)
            ColoredConsole.error(f'Crawl {crawler} failed.')
            continue
        i, e, f = await service.save(proxies)
        logger.info(
            f'{crawler["callable"]} page suc: {len(sus)}, fail: {len(fus)}'
            f'count: {len(proxies)} inserted: {len(i)}, exist: {len(e)}, failed: {len(f)}')
        res = {"crawler": crawler, "susurl": sus, "failurl": fus,
               "count": len(proxies), "insert": len(i),
               "exist": len(e), "fail": len(f)}
        if cb:
            cb(res)
        ret.append(res)
    return ret


def help():
    """Print help message."""
    print("""PARAM:
    -h, --help      Help.
    -c, --config    Config file path.
                    Default is `config.json`.
    -s, --semaphore The maximum number of concurrent.
                    Default is 10.""")
    exit(0)


def _cb(res: dict):
    """Callback of each crawler after run."""
    ColoredConsole.info(f'Finished {res["crawler"]["callable"]}.')
    if res["susurl"]:
        ColoredConsole.success(f'Success {len(res["susurl"])} pages. ')
    if res["failurl"]:
        ColoredConsole.error(f'Failed {len(res["failurl"])} pages.')
        for f in res['failurl']:
            ColoredConsole.debug(f)
    ColoredConsole.debug(f'Got {res["count"]} proxies.')
    if res["insert"]:
        ColoredConsole.success(f'Insert {res["insert"]} proxies.')
    if res["exist"]:
        ColoredConsole.debug(f'Exist {res["exist"]} proxies.')
    if res["fail"]:
        ColoredConsole.error(f'Fail {res["fail"]} proxies')


def statistics(res: list[dict]):
    tb = PrettyTable()
    tb.field_names = ['row', 'crawler', 'susurl', 'failurl',
                      'count', 'insert', 'exist', 'fail']
    csu, cfu, cc, ci, ce, cf = 0, 0, 0, 0, 0, 0
    for index, r in enumerate(res):
        tb.add_row([index+1, r['crawler']['callable'], len(r['susurl']), len(r['failurl']),
                    r['count'], r['insert'], r['exist'], r['fail']])
        csu += len(r['susurl'])
        cfu += len(r['failurl'])
        cc += r['count']
        ci += r['insert']
        ce += r['exist']
        cf += r['fail']
    tb.add_row(['Total', len(res), csu, cfu, cc, ci, ce, cf])
    tb.align = 'r'
    tb.align['crawler'] = 'l'
    return tb


def main(argv: list):
    cf = 'config.json'
    sem = CrawlsConfig.SEMAPHORE
    try:
        opts, _ = getopt(argv, "hcs:", ["help", "config=", "semaphore="])
    except GetoptError:
        print('test.py -i <inputfile> -o <outputfile>')
        exit(1)
    for opt, arg in opts:
        if opt in ['-h', '--help']:
            help()
        if opt in ['-c', '--config']:
            cf = arg
        if opt in ['-s', '--semaphore']:
            sem = int(arg)
    ConfigUtil(cf)  # Init once. Singleton.
    logger.info('Starting crawl...')
    ret = asyncio.run(run(CrawlsConfig.CRAWLERS, sem, _cb))
    logger.info('Crawl finished.')
    print(statistics(ret))


if __name__ == '__main__':
    main(sys.argv[1:])
