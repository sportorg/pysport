import unittest
from sportorg.core.version import *


class TestVersion(unittest.TestCase):
    def test_version(self):
        vals = [
            ((1, 13, 5, 35, 'v', 'beta'), 'v1.13.5-beta.35'),
            ((1, 13, 5, 0, 'v', 'beta'), 'v1.13.5-beta'),
            ((1, 13, 5, 0, '', 'beta'), '1.13.5-beta'),
            ((1, 13, 5), '1.13.5'),
            ((1, 13, 5, 564456), '1.13.5.564456'),
        ]
        for i in range(len(vals)):
            version = Version(*vals[i][0])
            self.assertEqual(vals[i][1], str(version), 'Version error, #iter-' + str(i))

    def test_version_eq(self):
        version1 = Version(0, 0, 25, 44)
        version2 = Version(0, 0, 25, 44)
        self.assertEqual(True, version1 == version2, 'Error')

    def test_version_is_compatible(self):
        version1 = Version(0, 1, 25, 44)
        version2 = Version(0, 1, 0)
        version3 = Version(1, 0, 25, 44)
        self.assertEqual(True, version1.is_compatible(version2), 'Error')
        self.assertEqual(False, version1.is_compatible(version3), 'Error')
        self.assertEqual(True, version2 <= version1 < version3, 'Error')
