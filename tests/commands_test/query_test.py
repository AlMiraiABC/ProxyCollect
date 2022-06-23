import json
from tempfile import mkstemp
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

from al_utils.console import ColoredConsole
from commands.query import main, save_to, to_table
from db.model import Anonymous, Protocol, Proxy, Verify
from services.query_service import QueryService


def mock_proxy(protocol=Protocol.HTTP, ip='2.2.2.2', port='3306'):
    return Proxy(protocol, ip, port, Verify.HTTP, Anonymous.HIGH)


async def mock_async_ret(ret):
    return ret

pmsgs: list[str] = []


def mock_cc_print(info, *args, **kwargs):
    pmsgs.append(info)


@patch.object(ColoredConsole, 'print', mock_cc_print)
class TestQuery(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        msgs = []

    def test_save_to_txt(self):
        N = 5
        _, fn = mkstemp()
        fn = fn+'.txt'
        save_to([mock_proxy() for _ in range(N)], fn)
        with open(fn, encoding='utf-8') as f:
            l = f.readlines()
        self.assertEqual(len(l), N)

    def test_save_to_json(self):
        N = 5
        _, fn = mkstemp()
        fn = fn+'.json'
        save_to([mock_proxy() for _ in range(N)], fn)
        with open(fn, encoding='utf-8') as f:
            l = json.load(f)
        self.assertEqual(len(l), N)

    def test_save_to_csv(self):
        N = 5
        _, fn = mkstemp()
        fn = fn+'.csv'
        save_to([mock_proxy() for _ in range(N)], fn)
        with open(fn, encoding='utf-8') as f:
            l = f.readlines()
        self.assertEqual(len(l), N+1)

    def test_save_to_other(self):
        N = 5
        _, fn = mkstemp()
        fn = fn+'.sql'
        with self.assertRaises(ValueError):
            save_to([mock_proxy() for _ in range(N)], fn)

    def test_to_table(self):
        N = 5
        proxies = [mock_proxy() for _ in range(N)]
        tb = to_table(proxies)
        self.assertEqual(len(tb.rows), N)

    @patch.object(QueryService, 'get_count', lambda *_, **__: mock_async_ret(5))
    def test_query_count(self):
        main(['-q', 'count', '-o', 'url'])
        self.assertEqual(pmsgs[0], 'COUNT: 5.')

    @patch.object(QueryService, 'get_check', lambda *_, **__: mock_async_ret(mock_proxy()))
    def test_query_check(self):
        main(['-q', 'check', '-o', 'url'])
        self.assertEqual(pmsgs[-1], 'http://2.2.2.2:3306')

    @patch.object(QueryService, 'get_random', lambda *_, **__: mock_async_ret([mock_proxy()]*5))
    def test_query_random(self):
        main(['-q', 'random', '-n', '5', '-o', 'url'])
        self.assertListEqual(pmsgs[-5:], ['http://2.2.2.2:3306']*5)

    @patch.object(QueryService, 'get', lambda *_, **__: mock_async_ret([mock_proxy()]*5))
    def test_query(self):
        main(['-o', 'url', '-n', '5'])
        self.assertListEqual(pmsgs[-5:], ['http://2.2.2.2:3306']*5)
