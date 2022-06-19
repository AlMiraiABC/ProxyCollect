from unittest import IsolatedAsyncioTestCase
from crawls.crawlers import kuaidaili
from services.crawl_service import CrawlService


async def mock_crawl(*args, **kwargs) -> str:
    return [args, kwargs]


class TestCrawlService(IsolatedAsyncioTestCase):

    async def asyncSetUp(self) -> None:
        self.service = CrawlService()
        return await super().asyncSetUp()

    def test_get_crawler_not_str(self):
        FUNC = kuaidaili
        crawler = self.service.get_crawler(FUNC)
        self.assertEqual(FUNC, crawler)

    def test_get_crawler_default(self):
        FUNC = 'kuaidaili'
        crawler = self.service.get_crawler(FUNC)
        self.assertEqual(kuaidaili.__name__, crawler.__name__)

    def test_get_crawler_not_found(self):
        FUNC = 'a.b.not_found'
        crawler = self.service.get_crawler(FUNC)
        self.assertIsNone(crawler)

    async def test_run(self):
        C = mock_crawl
        ret = await self.service.run(C, 1, 2, url='http://www.baidu.com')
        self.assertEqual([(1, 2), {'url': 'http://www.baidu.com'}], ret)

    async def test_run_unexist(self):
        C = 'a.b.not_found'
        with self.assertRaises(ImportError):
            await self.service.run(C, 1, 2, url='http://www.baidu.com')
