from pathlib import Path

import pytest

from sportorg.libs.iof.parser import parse


@pytest.mark.parametrize(
    'file_name',
    [
        'competitorList.xml',
        'entryList.xml',
        'resultList.xml',
        'resultList_ok.xml',
        'startList.xml',
    ],
)
def test_parse(file_name):
    assert parse(Path('tests/data/iof') / file_name)
