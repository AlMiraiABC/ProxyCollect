import asyncio
import sys
from getopt import GetoptError, getopt

from al_utils.console import ColoredConsole
from al_utils.logger import Logger
from util.config import CrawlsConfig, CrawlsCrawlerConfig
from services.crawl_service import CrawlService
from util.config_util import ConfigUtil

logger = Logger(__file__).logger
service = CrawlService()


async def run(conf: list[CrawlsCrawlerConfig], sem: int = 10) -> tuple[int, int, int]:
    inserted, exist, failed = 0, 0, 0
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
                proxies = await service.run(crawler['callable'], *crawler.get('args', ()), **crawler.get('kwargs', {}))
        except:
            logger.error(f'Crawl {crawler} failed.', exc_info=True)
            ColoredConsole.error(f'Crawl {crawler} failed.')
            continue
        i, e, f = await service.save(proxies)
        inserted += len(i)
        exist += len(e)
        failed += len(f)
        logger.info(
            f'{crawler["callable"]} inserted: {len(i)}, exist: {len(e)}, failed: {len(f)}')
        ColoredConsole.success(
            f'{crawler["callable"]} inserted {len(i)} proxies({len(e)} exist and {len(f)} failed.).')
    return inserted, exist, failed


def help():
    """Print help message."""
    print("""PARAM:
    -h, --help      Help.
    -c, --config    Config file path.
                    Default is `config.json`.
    -s, --semaphore The maximum number of concurrent.
                    Default is 10.""")
    exit(0)


def main(argv: list):
    cf = 'config.json'
    sem = CrawlsConfig.SEMEPHORE
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
    i, e, f = asyncio.run(run(CrawlsConfig.CRAWLERS, sem))
    logger.info(f'Crawl finished. Inserted: {i}, exist: {e}, failed: {f}')
    ColoredConsole.success(f'Insert {i} proxies.')
    ColoredConsole.warn(f'Exist {e} proxies.', emoji='📀 ')
    ColoredConsole.error(f'Failed {f} proxies.')


if __name__ == '__main__':
    main(sys.argv[1:])
