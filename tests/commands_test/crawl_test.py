from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

from services.crawl_service import CrawlService
from commands.crawl import run


async def mock_ret(v=None):
    return v


@patch.object(CrawlService, '__init__', lambda *_, **__: None)
class TestCrawl(IsolatedAsyncioTestCase):
    @patch.object(CrawlService, 'run', lambda *_, **__: mock_ret(([1]*3, [2]*2, [3]*1)))
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
        ret = await run(CONF)
        self.assertEqual(len(ret), len(CONF))
        ret0 = ret[0]
        self.assertEqual(ret0['susurl'], [2]*2)
        self.assertEqual(ret0['failurl'], [3]*1)
        self.assertEqual(ret0['count'], len([1]*3))
        self.assertEqual(ret0['insert'], len([1]*3))
        self.assertEqual(ret0['exist'], len([1]*2))
        self.assertEqual(ret0['fail'], len([1]*1))

    async def test_run_keyerr(self):
        CONF = [{}]
        ret = await run(CONF)
        self.assertListEqual(ret, [])
