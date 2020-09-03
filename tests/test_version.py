import pytest

from sportorg.common.version import *


@pytest.mark.parametrize(
    ('version', 'expected_string'),
    [
        ((1, 13, 5, 35, 'v', 'beta'), 'v1.13.5-beta.35'),
        ((1, 13, 5, 0, 'v', 'beta'), 'v1.13.5-beta'),
        ((1, 13, 5, 0, '', 'beta'), '1.13.5-beta'),
        ((1, 13, 5), '1.13.5'),
        ((1, 13, 5, 564456), '1.13.5.564456'),
    ],
)
def test_version(version, expected_string):
    result = Version(*version)
    assert str(result), expected_string


def test_version_eq():
    version1 = Version(0, 0, 25, 44)
    version2 = Version(0, 0, 25, 44)
    assert version1 == version2


def test_version_is_compatible():
    version1 = Version(0, 1, 25, 44)
    version2 = Version(0, 1, 0)
    version3 = Version(1, 0, 25, 44)
    assert version1.is_compatible(version2)
    assert not version1.is_compatible(version3)
    assert version2 <= version1 < version3
