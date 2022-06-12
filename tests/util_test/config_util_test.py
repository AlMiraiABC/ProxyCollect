from unittest import TestCase
from unittest.mock import patch

from util.config_util import ConfigUtil


@patch.object(ConfigUtil, '__init__', lambda *_, **__: None)
class TestConfigUtil(TestCase):
    def test__get_exist(self):
        KS = ['a']
        V = 'hello'
        CONFIG = {KS[0]: V}
        configutil = ConfigUtil()
        v = configutil._get(CONFIG, KS)
        self.assertEqual(V, v)

    def test__get_nest(self):
        KS = ['a', 'b']
        V = 'hello'
        CONFIG = {KS[0]: {KS[1]: V}}
        util = ConfigUtil()
        v = util._get(CONFIG, KS)
        self.assertEqual(V, v)

    def test__get_unexist(self):
        KS = ['a', 'b']
        V = 'hello'
        CONFIG = {KS[0]: V}
        configutil = ConfigUtil()
        v = configutil._get(CONFIG, KS)
        self.assertIsNone(v)
