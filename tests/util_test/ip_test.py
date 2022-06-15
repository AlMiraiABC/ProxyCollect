from unittest import IsolatedAsyncioTestCase, TestCase

from util.ip import PublicIP, is_formed_ipv4


class TestPublicIP(IsolatedAsyncioTestCase):
    async def test_all_ways(self):
        ip1 = await PublicIP.public_ip_from_aws()
        ip2 = await PublicIP.public_ip_from_httpbin()
        ip3 = await PublicIP.public_ip_from_ifconfig()
        ip4 = await PublicIP.public_ip_from_16yun()
        ip5 = await PublicIP.public_ip_from_ipcn()
        for ip in [ip2, ip3, ip4, ip5]:
            self.assertEqual(ip1, ip)


class TestIp(TestCase):
    def test_is_formed_ipv4(self):
        t = is_formed_ipv4
        self.assertTrue(t('192.168.1.1'))  # normal
        self.assertTrue(t('127.0.0.1'))  # localhost
        self.assertTrue(t('0.0.0.0'))  # minimum
        self.assertTrue(t('255.255.255.255'))  # maximum
        self.assertFalse(t('256.256.256.256'))  # out of upper bound
        self.assertFalse(t('999.999.999.999'))  # out of range
        self.assertFalse(t('1.2.3'))  # missing one part
        self.assertTrue(t('1.2.3.4'))  # fix above
        self.assertTrue(t('01.01.01.1'))  # starts with 0
        self.assertFalse(t('-1.-1.1.1'))  # out of lower bound
        self.assertFalse(t('256.255.255.255'))  # only one part out of range
        self.assertFalse(t('abc192.168.1.1'))  # starts with non-digits
        self.assertFalse(t(''))  # empty string
        self.assertFalse(t(None))  # None param
        self.assertTrue(t('  0.0.0.0  '))  # with blanks
