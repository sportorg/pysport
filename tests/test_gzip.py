import pytest

from sportorg.models.memory import Group, Organization, Person, race
from sportorg.modules.backup.file import File
from sportorg.modules.configs.configs import Config


@pytest.fixture()
def use_gzip():
    old_value = Config().configuration.get("save_in_gzip", False)
    Config().configuration.set("save_in_gzip", True)
    yield
    Config().configuration.set("save_in_gzip", old_value)


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
