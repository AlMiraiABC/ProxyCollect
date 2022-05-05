from unittest import TestCase

from util.ip_util import IpUtil


class TestIpUtil(TestCase):
    def test_is_formed_ipv4(self):
        t=IpUtil.is_formed_ipv4
        self.assertTrue(t('192.168.1.1')) # normal
        self.assertTrue(t('127.0.0.1')) # localhost
        self.assertTrue(t('0.0.0.0')) # minimum
        self.assertTrue(t('255.255.255.255')) # maximum
        self.assertFalse(t('256.256.256.256')) # out of upper bound
        self.assertFalse(t('999.999.999.999')) # out of range
        self.assertFalse(t('1.2.3'))  # missing one part
        self.assertTrue(t('1.2.3.4')) # fix above
        self.assertTrue(t('01.01.01.1')) # starts with 0
        self.assertFalse(t('-1.-1.1.1')) # out of lower bound
        self.assertFalse(t('256.255.255.255')) # only one part out of range
        self.assertFalse(t('abc192.168.1.1')) # starts with non-digits
        self.assertFalse(t('')) # empty string
        self.assertFalse(t(None)) # None param
        self.assertTrue(t('  0.0.0.0  ')) # with blanks
