import unittest

from sportorg import config


class TestISS(unittest.TestCase):

    def setUp(self):
        print('=========>', self.__class__.__name__, self._testMethodName)
        with open('sportorg.iss') as f:
            self.data = f.readlines()

    def test_app_version(self):
        for item in self.data:
            if '#define MyAppVersion ' in item:
                self.assertTrue(str(config.VERSION) in item, '{} not in "{}"'.format(config.VERSION, item))
                return
        self.fail('Not app version')

    def test_version_info(self):
        for item in self.data:
            if '#define MyVersionInfoVersion ' in item:
                self.assertTrue(config.VERSION.file in item, '{} not in "{}"'.format(config.VERSION.file, item))
                return
        self.fail('Not version info')
