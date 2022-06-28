import json
from unittest import IsolatedAsyncioTestCase, skip
from unittest.mock import patch
from aioresponses import aioresponses

import requests
from db.model import Anonymous, Protocol, Proxy, Verify
from util.config import ValidConfig

from util.valid import BaseValidCallables, Valid, ValidHelper


class MockResp:
    """Requests response"""

    def __init__(self, status_code: int, text: str, reason: str = ''):
        self.status_code = status_code
        self.text = text
        self.content = text
        self.json = lambda: json.loads(text)
        self.reason = reason


def mock_proxy(protocol=Protocol.HTTP, ip='2.2.2.2', port='3306'):
    return Proxy(protocol, ip, port, Verify.HTTP, Anonymous.HIGH)


class TestValidHelper(IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ValidHelper.PUBLIC_IP = '1.1.1.1'

    def test_check_anonymous_trans(self):
        anon = ValidHelper.check_anonymous('', '1.1.1.1, 2.2.2.2')
        self.assertEqual(anon, Anonymous.TRANSPARENT)

    def test_check_anonymous_anon(self):
        anon = ValidHelper.check_anonymous(mock_proxy(), '2.2.2.2, 3.3.3.3')
        self.assertEqual(anon, Anonymous.ANONYMOUS)

    def test_check_anonymous_high(self):
        anon = ValidHelper.check_anonymous(mock_proxy(), '127.0.0.1')
        self.assertEqual(anon, Anonymous.HIGH)

    @patch.object(requests, 'get', lambda *_, **__: MockResp(200, '1.1.1.1, 2.2.2.2'))
    def test_sync_get(self):
        anon = ValidHelper.sync_get('', mock_proxy(), 30, lambda x: x.text)
        self.assertEqual(anon, Anonymous.TRANSPARENT)

    @patch.object(requests, 'get', lambda *_, **__: MockResp(404, ''))
    def test_sync_get_connectionerror(self):
        with self.assertRaises(ConnectionError):
            ValidHelper.sync_get('', mock_proxy())

    @aioresponses()
    async def test_async_get(self, mock: aioresponses):
        mock.get('https://a.co', body='1.1.1.1, 2.2.2.2')
        anon = await ValidHelper.async_get('https://a.co', mock_proxy())
        self.assertEqual(anon, Anonymous.TRANSPARENT)

    @aioresponses()
    async def test_async_get_connectionerror(self, mock: aioresponses):
        mock.get('https://a.co', status=404)
        with self.assertRaises(ConnectionError):
            await ValidHelper.async_get('https://a.co', mock_proxy())


class TestValid(IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.valid = Valid('1.1.1.1', 30)

    @patch.object(requests, 'get', lambda *_, **__: MockResp(200, '1.1.1.1, 2.2.2.2'))
    def test_sync_valid(self):
        speed, anon = self.valid.sync_valid(mock_proxy())
        self.assertNotEqual(speed, -1)
        self.assertEqual(anon, Anonymous.TRANSPARENT)

    @patch.object(requests, 'get', lambda *_, **__: MockResp(404, ''))
    def test_sync_valid_connectionerror(self):
        speed, anon = self.valid.sync_valid(mock_proxy())
        self.assertEqual(speed, -1)
        self.assertEqual(anon, Anonymous.TRANSPARENT)

    @aioresponses()
    async def test_async_valid(self, mock: aioresponses):
        mock.get('http://checkip.nmtsoft.net/forwarded',
                 body='1.1.1.1, 2.2.2.2')
        speed, anon = await self.valid.async_valid(mock_proxy())
        self.assertNotEqual(speed, -1)
        self.assertEqual(anon, Anonymous.TRANSPARENT)

    @aioresponses()
    async def test_async_valid_connectionerror(self, mock: aioresponses):
        mock.get('http://checkip.nmtsoft.net/forwarded', status=404)
        speed, anon = await self.valid.async_valid(mock_proxy())
        self.assertEqual(speed, -1)
        self.assertEqual(anon, Anonymous.TRANSPARENT)

    @patch.object(requests, 'get', lambda *_, **__: MockResp(200, '3.3.3.3'))
    def test_sync_http(self):
        anon = self.valid.sync_http(mock_proxy(), 'nmtsoft')
        self.assertEqual(anon, Anonymous.HIGH)

    def test_sync_http_unattr(self):
        with self.assertRaises(AttributeError):
            self.valid.sync_http(mock_proxy(), 30, 'unexist')

    @patch.object(requests, 'get', lambda *_, **__: MockResp(200, '3.3.3.3'))
    def test_sync_https(self):
        anon = self.valid.sync_https(mock_proxy(), 'nmtsoft')
        self.assertEqual(anon, Anonymous.HIGH)

    def test_sync_https_unattr(self):
        with self.assertRaises(AttributeError):
            self.valid.sync_https(mock_proxy(), 30, 'unexist')

    @aioresponses()
    async def test_async_http(self, mock: aioresponses):
        mock.get('http://checkip.nmtsoft.net/forwarded',
                 body='3.3.3.3')
        anon = await self.valid.async_http(mock_proxy(), 'nmtsoft')
        self.assertEqual(anon, Anonymous.HIGH)

    async def test_async_http_unattr(self):
        with self.assertRaises(AttributeError):
            await self.valid.async_http(mock_proxy(), 'unexist')

    @aioresponses()
    async def test_async_https(self, mock: aioresponses):
        mock.get('https://checkip.nmtsoft.net/forwarded',
                 body='3.3.3.3')
        anon = await self.valid.async_https(mock_proxy(), 'nmtsoft')
        self.assertEqual(anon, Anonymous.HIGH)

    async def test_async_https_unattr(self):
        with self.assertRaises(AttributeError):
            await self.valid.async_https(mock_proxy(), 'unexist')

    def test_get_valid_methods(self):
        class T(BaseValidCallables):
            def sync_a():
                pass

            def sync_b():
                pass

            async def async_a():
                pass

            async def async_b():
                pass
        syncs,  asyncs = self.valid.get_valid_methods(T)
        self.assertListEqual(
            [m.__name__ for m in [T.sync_a, T.sync_b]],
            [m.__name__ for m in syncs]
        )
        self.assertListEqual(
            [m.__name__ for m in [T.async_a, T.async_b]],
            [m.__name__ for m in asyncs]
        )


@skip("""A real proxy and always change.
Don't run in CI.
Result is uncertain.""")
class TestValidGround(IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.valid = Valid(ValidConfig.PUBLIC_IP, ValidConfig.TIMEOUT)
        cls.proxy = Proxy(Protocol.HTTP, '58.20.235.180',
                          9091, Verify.HTTP, Anonymous.TRANSPARENT)

    def test_sync_valid(self):
        t, a = self.valid.sync_valid(self.proxy)
        print(t, a)

    async def test_async_valid(self):
        t, a = await self.valid.async_valid(self.proxy)
        print(t, a)
