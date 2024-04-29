import pytest

from sportorg.gui.tabs.memory_model import AbstractSportOrgMemoryModel
from sportorg.language import translate


@pytest.mark.parametrize(
    'pattern, value, expected',
    [
        ('', '', True),
        ('', 'Ivan', False),
        ('Ivan', '', False),
        ('Ivan', 'Ivan', True),
        ('Ivan', 'Aleksey', False),
        ('ivan', 'Ivan', False),
        ('Ivan', 'Ivanov', False),
        ('Ivan', 'Ivanov Ivan', False),
        ('Ivan', 'Ivanov Ivan Ivanovich', False),
        ('Иван', 'Иван', True),
        ('1993', '1993', True),
        ('1993', '4651993', False),
    ],
)
def test_filter_equal_to_action(pattern, value, expected):
    model = AbstractSportOrgMemoryModel
    check = model.compile_regex(translate('equal to'), pattern)
    result = model.match_value(check, str(value))
    assert result == expected


@pytest.mark.parametrize(
    'pattern, value, expected',
    [
        ('', '', True),
        ('', 'Ivan', True),
        ('Ivan', '', False),
        ('Ivan', 'Ivan', True),
        ('Ivan', 'Aleksey', False),
        ('ivan', 'Ivan', False),
        ('Ivan', 'Ivanov', True),
        ('Ivan', 'Sidorov Ivan', True),
        ('Ivan', 'Sidorov Ivan Petrovich', True),
        ('Иван', 'Иван', True),
        ('1993', '1993', True),
        ('1993', '4651993', True),
    ],
)
def test_filter_contain_to_action(pattern, value, expected):
    model = AbstractSportOrgMemoryModel
    check = model.compile_regex(translate('contain'), pattern)
    result = model.match_value(check, str(value))
    assert result == expected


@pytest.mark.parametrize(
    'pattern, value, expected',
    [
        ('', '', True),
        ('', 'Ivan', False),
        ('Ivan', '', True),
        ('Ivan', 'Ivan', False),
        ('Ivan', 'Aleksey', True),
        ('ivan', 'Ivan', True),
        ('Ivan', 'Ivanov', False),
        ('Ivan', 'Sidorov Ivan', False),
        ('Ivan', 'Sidorov Ivan Petrovich', False),
        ('Иван', 'Иван', False),
        ('1993', '1993', False),
        ('1993', '4651993', False),
    ],
)
def test_filter_doesnt_contain_to_action(pattern, value, expected):
    model = AbstractSportOrgMemoryModel
    check = model.compile_regex(translate("doesn't contain"), pattern)
    result = model.match_value(check, str(value))
    assert result == expected


@pytest.mark.parametrize(
    'pattern, value, expected',
    [
        ('', '', True),
        ('', 'Ivan', True),
        ('Ivan', '', True),
        ('Ivan', 'Ivan', True),
        ('Ivan', 'Aleksey', True),
    ],
)
def test_filter_wrong_action(pattern, value, expected):
    model = AbstractSportOrgMemoryModel
    check = model.compile_regex(translate('wrong action'), pattern)
    result = model.match_value(check, value)
    assert result == expected
