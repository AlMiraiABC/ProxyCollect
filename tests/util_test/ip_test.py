from unittest import IsolatedAsyncioTestCase

from util.ip import PublicIP


class TestPublicIP(IsolatedAsyncioTestCase):
    async def test_all_ways(self):
        ip1 = await PublicIP.public_ip_from_aws()
        ip2 = await PublicIP.public_ip_from_httpbin()
        ip3 = await PublicIP.public_ip_from_ifconfig()
        ip4 = await PublicIP.public_ip_from_16yun()
        ip5 = await PublicIP.public_ip_from_ipcn()
        for ip in [ip2, ip3, ip4, ip5]:
            self.assertEqual(ip1, ip)
