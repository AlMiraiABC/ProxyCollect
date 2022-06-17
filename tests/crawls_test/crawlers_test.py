from unittest import IsolatedAsyncioTestCase

from aioresponses import aioresponses
from crawls.crawlers import *


class TestCrawlersKuaidaili(IsolatedAsyncioTestCase):
    @aioresponses()
    async def test_kuaidaili(self, mocked: aioresponses):
        inha_body = '''
            <tr>
                <td data-title="IP">103.37.141.69</td>
                <td data-title="PORT">80</td>
                <td data-title="匿名度">高匿名</td>
                <td data-title="类型">HTTP</td>
                <td data-title="位置">中国 北京  </td>
                <td data-title="响应速度">6秒</td>
                <td data-title="最后验证时间">2022-06-17 20:31:01</td>
            </tr>

            <tr>
                <td data-title="IP">58.20.184.187</td>
                <td data-title="PORT">9091</td>
                <td data-title="匿名度">高匿名</td>
                <td data-title="类型">HTTP</td>
                <td data-title="位置">中国 湖南 衡阳 联通</td>
                <td data-title="响应速度">0.5秒</td>
                <td data-title="最后验证时间">2022-06-17 19:31:01</td>
            </tr>
            '''
        mocked.get(re.compile('https://www.kuaidaili.com/free/inha/\d+/'),
                   status=200, body=inha_body)
        intr_body = '''
            <tr>
                <td data-title="IP">47.92.113.71</td>
                <td data-title="PORT">80</td>
                <td data-title="匿名度">透明</td>
                <td data-title="类型">HTTP</td>
                <td data-title="位置">中国 北京  联通</td>
                <td data-title="响应速度">1秒</td>
                <td data-title="最后验证时间">2022-06-17 21:31:01</td>
            </tr>

            <tr>
                <td data-title="IP">121.8.215.106</td>
                <td data-title="PORT">9797</td>
                <td data-title="匿名度">透明</td>
                <td data-title="类型">HTTP</td>
                <td data-title="位置">广东省广州市  电信</td>
                <td data-title="响应速度">1秒</td>
                <td data-title="最后验证时间">2022-06-17 20:31:01</td>
            </tr>
            '''
        mocked.get(re.compile('https://www.kuaidaili.com/free/intr/\d+/'),
                   status=200, body=intr_body)
        proxies, s, f = await kuaidaili(1, 1)
        self.assertEqual(len(proxies), 4)
        self.assertEqual(len(s), 2)
        self.assertEqual(len(f), 0)

    @aioresponses()
    async def test_kuaidaili_resp_err(self, mocked: aioresponses):
        mocked.get(re.compile('https://www.kuaidaili.com/free/inha/\d+/'),
                   status=500)
        mocked.get(re.compile('https://www.kuaidaili.com/free/intr/\d+/'),
                   status=404)
        proxies, s, f = await kuaidaili(1, 5)
        self.assertEqual(len(proxies), 0)
        self.assertEqual(len(s), 0)
        self.assertEqual(len(f), 10)

    @aioresponses()
    async def test_kuaidaili_convert_err(self, mocked: aioresponses):
        inha_body = '''
            <tr>
                <td data-title="IP">103.37.141.69</td>
                <td data-title="PORT">abcdefg</td>
                <td data-title="匿名度">高匿名</td>
                <td data-title="类型">HTTP</td>
                <td data-title="位置">中国 北京  </td>
                <td data-title="响应速度">6秒</td>
                <td data-title="最后验证时间">2022-06-17 20:31:01</td>
            </tr>

            <tr>
                <td data-title="IP">58.20.184.187</td>
                <td data-title="PORT">9091</td>
                <td data-title="匿名度">高匿名</td>
                <td data-title="类型">HTTP</td>
                <td data-title="位置">中国 湖南 衡阳 联通</td>
                <td data-title="响应速度">0.5秒</td>
                <td data-title="最后验证时间">2022-06-17 19:31:01</td>
            </tr>
            '''
        mocked.get(re.compile('https://www.kuaidaili.com/free/inha/\d+/'),
                   status=200, body=inha_body)
        intr_body = '''
            <tr>
                <td data-title="IP">47.92.113.71</td>
                <td data-title="PORT">80</td>
                <td data-title="匿名度">透明</td>
                <td data-title="类型">FTP</td>
                <td data-title="位置">中国 北京  联通</td>
                <td data-title="响应速度">1秒</td>
                <td data-title="最后验证时间">2022-06-17 21:31:01</td>
            </tr>

            <tr>
                <td data-title="IP">121.8.215.106</td>
                <td data-title="PORT">9797</td>
                <td data-title="匿名度">透明</td>
                <td data-title="类型">HTTP</td>
                <td data-title="位置">广东省广州市  电信</td>
                <td data-title="响应速度">1秒</td>
                <td data-title="最后验证时间">2022-06-17 20:31:01</td>
            </tr>
            '''
        mocked.get(re.compile('https://www.kuaidaili.com/free/intr/\d+/'),
                   status=200, body=intr_body)
        proxies, s, f = await kuaidaili(1, 1)
        self.assertEqual(len(proxies), 2)
        self.assertEqual(len(s), 2)
        self.assertEqual(len(f), 0)
