import importlib.util
from unittest import TestCase

from util.implib import *
from util.implib import import_function


class TestGetModuleSpec(TestCase):
    def test_module_spec(self):
        NAME = 'unittest.mock'
        spec = get_module_spec(NAME)
        self.assertIsNotNone(spec)

    def test_module_spec_unexist(self):
        NAME = 'unittest.unexist'
        spec = get_module_spec(NAME)
        self.assertIsNone(spec)


class TestImportModuleFromSpec(TestCase):
    def test_import_module_spec_none(self):
        NAME = None
        spec = get_module_spec(NAME)
        self.assertIsNone(spec)

    def test_import_module_from_spec(self):
        spec = importlib.util.find_spec('unittest.mock')
        module = import_module_from_spec(spec)
        self.assertIsNotNone(module)


class TestImportModule(TestCase):
    def test_import_module(self):
        NAME = 'unittest.mock'
        module = import_module(NAME)
        self.assertIsNotNone(module)

    def test_import_module_none(self):
        NAME = None
        module = import_module(NAME)
        self.assertIsNone(module)

    def test_import_module_exist(self):
        NAME = 'unexist.unexist'
        module = import_module(NAME)
        self.assertIsNone(module)


class TestImportFunction(TestCase):
    def test_import_function(self):
        NAME = 'time.time'
        func = import_function(NAME)
        self.assertIsNotNone(func)
        r = func()
        self.assertTrue(r)

    def test_import_function_unstr(self):
        FUNC = import_function
        func = import_function(FUNC)
        self.assertEqual(FUNC, func)

    def test_import_function_unexist(self):
        NAME = 'unittest.unexist_func'
        func = import_function(NAME)
        self.assertIsNone(func)

    def test_import_function_malformed(self):
        NAME = 'abcdefg'
        func = import_function(NAME)
        self.assertIsNone(func)
