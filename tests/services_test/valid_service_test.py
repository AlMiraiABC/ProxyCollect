from unittest import IsolatedAsyncioTestCase, skip
from unittest.mock import patch

from db.dbutil import DbUtil
from db.model import Anonymous, Protocol, StoredProxy, Verify
from services.valid_service import ValidService
from util.valid import Valid


async def mock_proxy(anonymous=Anonymous.HIGH, speed=1.0):
    return StoredProxy(1, Protocol.HTTP, '127.0.0.1',
                       33, Verify, 100, anonymous, speed=speed)


async def mock_proxies(num=55):
    proxy = StoredProxy(1, Protocol.HTTP, '127.0.0.1',
                        33, Verify, 100, Anonymous.HIGH)
    return [proxy for _ in range(num)]


async def mock_async(*args):
    return args


@patch.object(DbUtil, '__init__', lambda *_, **__: None)
@patch.object(Valid, '__init__', lambda *_, **__: None)
class TestValidService(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.service = ValidService(Valid('127.0.0.1', 30))

    @patch.object(DbUtil, 'gets', lambda *_, **__: mock_proxies(5))
    async def test_get_patch(self):
        proxies = await self.service.get_patch()
        self.assertEqual(self.service._cursor, 5)
        self.assertEqual(len(proxies), 5)

    @patch.object(DbUtil, 'gets', lambda *_, **__: mock_proxies(0))
    async def test_get_patch_empty(self):
        proxies = await self.service.get_patch()
        self.assertEqual(self.service._cursor, -1)
        self.assertEqual(len(proxies), 0)

    @skip('return self._db._update(...)')
    @patch.object(Valid, 'async_valid', lambda *_, **__: mock_async())
    @patch.object(DbUtil, '_update', lambda *_: mock_proxy())
    async def test_update(self):
        pass

    @patch.object(ValidService, 'update', lambda *_, **__: mock_proxy())
    async def test_valid_proxies(self):
        S = 5
        for i in range(S):
            await self.service._queue.put(i)
        updated = await self.service.valid_proxies()
        self.assertEqual(len(updated), S)

    async def test_valid_proxies_empty(self):
        updated = await self.service.valid_proxies()
        self.assertListEqual(updated, [])

    @patch.object(ValidService, 'valid_proxies', lambda *_, **__: mock_async(None))
    @patch.object(ValidService, 'get_patch', lambda *_, **__: mock_proxies(5))
    async def test_run_patch(self):
        await self.service.run_patch()
        self.assertEqual(self.service._queue.qsize(), 5)

    @patch.object(ValidService, 'get_patch', lambda *_, **__: mock_proxies(0))
    async def test_run_patch_empty(self):
        await self.service.run_patch()
        self.assertEqual(self.service._queue.qsize(), 0)

    async def test__count(self):
        proxies = []
        fails = [None]*10
        proxies.extend(fails)
        timeouts = [await mock_proxy(speed=-1)]*5
        proxies.extend(timeouts)
        sucs = [await mock_proxy()]*3
        proxies.extend(sucs)
        c, f, t = self.service._count(proxies)
        self.assertEqual(len(proxies), c)
        self.assertEqual(len(fails), f)
        self.assertEqual(len(timeouts), t)
