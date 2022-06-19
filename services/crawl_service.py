from typing import Awaitable, Callable

from crawls.crawlers import CRAW_RET
from util.implib import import_function


class CrawlService:
    def __init__(self):
        pass

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
