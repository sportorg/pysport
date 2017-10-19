import unittest
from sportorg.lib.ocad import ocad
from sportorg.config import base_dir


class TestOcadMethods(unittest.TestCase):

    def setUp(self):
        file = base_dir('test', 'CoursesV8.txt')
        self.classes_v8 = ocad.parse_txt_v8(file)

    def test_v8_parse(self):
        file = base_dir('test', 'CoursesV8.txt')
        self.classes_v8.parse(file)

    def test_courses(self):
        courses = self.classes_v8.courses

    def test_groups(self):
        groups = self.classes_v8.groups

    def test_get_item(self):
        ocad.ClassesV8.get_courses("M16;Normal Course;0;5.700;130;S1;0.216;47;0.216;120;0.280;115;0.229;F1")
        len(ocad.ClassesV8.get_courses("M16;Normal Course;0;5.700;130;S1;0.216;47;0.216;120;0.280;115;0.229;F1"))
        course = ocad.ClassesV8.get_course("M16;Normal Course;0;5.700;130;S1;0.216;47;0.216;120;0.229;F1".split(";"))
        for order, c in course.controls.items():
            code = c.code
        with self.assertRaises(TypeError):
            ocad.ClassesV8.get_courses({})
        with self.assertRaises(TypeError):
            ocad.ClassesV8.get_courses(0)

    def tearDown(self):
        del self.classes_v8
