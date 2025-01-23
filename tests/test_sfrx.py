from sportorg.libs.sfr import sfrximporter
from sportorg.models.memory import (
    Group,
    Organization,
    Person,
    Qualification,
    find,
    race,
)


def test_import_sfrx():
    sfrximporter.import_sfrx("tests/data/sfrx_file.sfrx")
    person = find(race().persons, name="СЕМЕН", surname="НИКИТИН")
    assert isinstance(person, Person), "Not person"
    assert isinstance(person.group, Group), "Not group"
    assert person.group.name == "М14", "Group name error"
    assert isinstance(person.organization, Organization), "Not organization"
    assert (
        person.organization.name == "СДЮСШ Балт. берег Peterhof"
    ), "Organization name error"
    assert person.get_year() == 2009, "Year error"
    assert person.card_number == 0, "Card number error"
    assert person.qual == Qualification.I_Y, "Qualification error"
