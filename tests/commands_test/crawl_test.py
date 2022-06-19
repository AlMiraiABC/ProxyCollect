from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

from services.crawl_service import CrawlService
from commands.crawl import run


async def mock_ret(v=None):
    return v


@patch.object(CrawlService, '__init__', lambda *_, **__: None)
class TestCrawl(IsolatedAsyncioTestCase):
    @patch.object(CrawlService, 'run', lambda *_, **__: mock_ret([]))
    @patch.object(CrawlService, 'save', lambda *_, **__: mock_ret(([1]*3, [1]*2, [1]*1)))
    async def test_run(self):
        CONF = [
            {
                'callable': 'c1',
            },
            {
                'callable': 'c2',
            },
            {
                'callable': 'c3',
            }
        ]
        inserted, exist, failed = await run(CONF)
        self.assertEqual(inserted, 3*len(CONF))
        self.assertEqual(exist, 2*len(CONF))
        self.assertEqual(failed, 1*len(CONF))

    async def test_run_keyerr(self):
        CONF = [{}]
        inserted, exist, failed = await run(CONF)
        self.assertEqual(inserted, 0)
        self.assertEqual(exist, 0)
        self.assertEqual(failed, 0)
