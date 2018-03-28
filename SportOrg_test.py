import sys
import unittest

from sportorg import config

print('Test {} {}'.format(config.NAME, config.VERSION))

testmodules = [
    'iss_test',
    'sportorg.language_test',
    'sportorg.core.otime_test',
    'sportorg.core.version_test',
    'sportorg.libs.winorient.wdb_test',
    'sportorg.libs.ocad.ocad_test',
    'sportorg.modules.backup.json_test',
    'sportorg.modules.testing.memory_test',
    'sportorg.modules.winorient.winorient_test',
    'sportorg.modules.ocad.ocad_test',
]

suite = unittest.TestSuite()

for t in testmodules:
    try:
        # If the module defines a suite() function, call it to get the suite.
        mod = __import__(t, globals(), locals(), ['suite'])
        suitefn = getattr(mod, 'suite')
        suite.addTest(suitefn())
    except (ImportError, AttributeError):
        # else, just load all the test cases from the module.
        suite.addTest(unittest.defaultTestLoader.loadTestsFromName(t))

sys.exit(not unittest.TextTestRunner().run(suite).wasSuccessful())
