import unittest


def test():
    def get_module(module):
        return 'sportorg.modules.testing.' + module
    suite = unittest.TestSuite()

    suite.addTest(unittest.defaultTestLoader.loadTestsFromName(get_module('memory_test')))

    unittest.TextTestRunner().run(suite)
