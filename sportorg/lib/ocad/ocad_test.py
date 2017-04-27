import unittest
from sportorg.lib.ocad import ocad


class TestStringMethods(unittest.TestCase):

    def setUp(self):
        file = ""
        self.classes_v8 = ocad.parse_txt_v8(file)

    # def test_v8_parse(self):
    #     file = ""
    #     self.classes_v8.parse(file)

    def test_courses(self):
        print(self.classes_v8.courses)

    def test_groups(self):
        print(self.classes_v8.groups)

    def test_get_item(self):
        print(ocad.ClassesV8.get_courses("M16;Normal Course;0;5.700;130;S1;0.216;47;0.216;120;0.280;115;0.229;F1"))
        print(ocad.ClassesV8.get_course("M16;Normal Course;0;5.700;130;S1;0.216;47;0.216;120;0.229;F1".split(";")))
        with self.assertRaises(TypeError):
            ocad.ClassesV8.get_courses({})
        with self.assertRaises(TypeError):
            ocad.ClassesV8.get_courses(0)

    def tearDown(self):
        del self.classes_v8


if __name__ == '__main__':
    unittest.main()
