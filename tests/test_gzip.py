import pytest

from sportorg import settings
from sportorg.models.memory import Group, Organization, Person, race
from sportorg.modules.backup.file import File


@pytest.fixture()
def use_gzip():
    old_value = settings.SETTINGS.file_save_in_gzip
    settings.SETTINGS.file_save_in_gzip = True
    yield
    settings.SETTINGS.file_save_in_gzip = old_value


@pytest.mark.usefixtures("use_gzip")
def test_save_and_open_gzip():
    File("tests/data/test.json").open()
    File("tests/data/test.json.tmp").save()
    File("tests/data/test.json.tmp").open()
    r = race()
    person = None
    for p in r.persons:
        if p.full_name == "Akhtarov Danil" and p.card_number == 9777775:
            person = p
    assert isinstance(person, Person), "Import person failed"
    assert isinstance(person.group, Group), "Import group failed"
    assert isinstance(person.organization, Organization), "Import organization failed"
