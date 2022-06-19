from typing import Awaitable, Callable

from al_utils.logger import Logger
from crawls.crawlers import CRAW_RET
from db.dbutil import DbUtil
from db.model import Proxy
from util.implib import import_function

logger = Logger(__file__).logger


class CrawlService:
    def __init__(self):
        self._db = DbUtil()

    def get_crawler(self, crawler: str | Callable) -> Callable:
        """
        Get a crawler.

        :param cralwer: Full-qualified crawler name or a function.
                `<module>.<crawler_func>`. Default `<module>` is `crawls.crawlers` if does not contain `<module>`.
        :return: Callable if it exists, None otherwise.
        """
        if not isinstance(crawler, str):
            return crawler
        if '.' not in crawler:
            crawler = f'crawls.crawlers.{crawler}'
        return import_function(crawler)

    async def run(self, crawler: str | Callable[[any], Awaitable[CRAW_RET]], *args, **kwargs) -> CRAW_RET:
        """
        Run a crawler.

        :param cralwer: Full-qualified crawler name or a function.
                `<module>.<crawler_func>`. Default `<module>` is `crawls.crawlers` if does not contain `<module>`.
        :param args: Arguments for :param:`cralwer`.
        :param kwargs: Keyword arguments for :param:`cralwer`.
        :return: Execute result of :param:`cralwer`.
        :raises ImportError: :param:`cralwer` not found.
        """
        crawler = self.get_crawler(crawler)
        if crawler is None:
            raise ImportError(f'Crawler {crawler} not found.')
        return await crawler(*args, **kwargs)

    async def save(self, proxies: list[Proxy]) -> tuple[list[Proxy], list[Proxy], list[Proxy]]:
        """
        Save proxies to db.

        :return: (inserted, exist, failed)
        """
        inserted: list[Proxy] = []
        exist: list[Proxy] = []
        failed: list[Proxy] = []
        for proxy in proxies:
            try:
                i = self._db.try_insert(proxy)
                if i:
                    inserted.append(i)
                else:
                    exist.append(proxy)
            except:
                logger.warning(f'Failed to insert proxy {proxy}.',
                               exc_info=True)
                failed.append(proxy)
        return inserted, exist, failed
