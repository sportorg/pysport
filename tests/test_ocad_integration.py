from sportorg.models.memory import Course, find, race
from sportorg.modules.ocad import ocad


def test_import_txt_v8():
    ocad.import_txt_v8('tests/data/CoursesV8.txt')
    course = find(race().courses, name='999')
    assert isinstance(course, Course), 'Not course'
    assert course.length == 4400
    assert course.climb == 0
    assert len(course.controls) == 14
    assert course.controls[3].code == '34'
    assert course.controls[3].length == 316
