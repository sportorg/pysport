import pytest

from sportorg.config import base_dir
from sportorg.libs.ocad import ocad


@pytest.fixture()
def classes_v8(request):
    file = base_dir('tests', 'data', 'CoursesV8.txt')
    return ocad.parse_txt_v8(file)


def test_v8_parse(classes_v8):
    file = base_dir('tests', 'data', 'CoursesV8.txt')
    assert classes_v8.parse(file)


def test_courses(classes_v8):
    assert classes_v8.courses


def test_groups(classes_v8):
    assert classes_v8.groups


def test_get_item():
    assert ocad.ClassesV8.get_courses(
        'M16;Normal Course;0;5.700;130;S1;0.216;47;0.216;120;0.280;115;0.229;F1'
    )
    assert len(
        ocad.ClassesV8.get_courses(
            'M16;Normal Course;0;5.700;130;S1;0.216;47;0.216;120;0.280;115;0.229;F1'
        )
    )
    course = ocad.ClassesV8.get_course(
        'M16;Normal Course;0;5.700;130;S1;0.216;47;0.216;120;0.229;F1'.split(';')
    )
    for _, c in course.controls.items():
        assert c.code

    with pytest.raises(TypeError):
        ocad.ClassesV8.get_courses({})
    with pytest.raises(TypeError):
        ocad.ClassesV8.get_courses(0)
