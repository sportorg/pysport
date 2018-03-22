import unittest

from sportorg.models.memory import race, find, Course
from sportorg.modules.ocad import ocad


class TestOcad(unittest.TestCase):
    def setUp(self):
        print('=========>', self.__class__.__name__, self._testMethodName)

    def test_import_txt_v8(self):
        ocad.import_txt_v8('test/CoursesV8.txt')
        course = find(race().courses, name='999')
        self.assertIsInstance(course, Course, 'Not course')
        self.assertEqual(course.length, 4400)
        self.assertEqual(course.climb, 0)
        self.assertEqual(len(course.controls), 14)
        self.assertEqual(course.controls[3].code, '34')
        self.assertEqual(course.controls[3].length, 316)
