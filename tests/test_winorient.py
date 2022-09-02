from sportorg.models.memory import (
    Group,
    Organization,
    Person,
    Qualification,
    find,
    race,
)
from sportorg.modules.winorient import winorient


def test_import_csv():
    winorient.import_csv('tests/data/5979_csv_wo.csv')
    person = find(race().persons, name='Сергей', surname='Добрынин')
    assert isinstance(person, Person), 'Not person'
    assert isinstance(person.group, Group), 'Not group'
    assert person.group.name == 'МУЖЧИНЫ', 'Group name error'
    assert isinstance(person.organization, Organization), 'Not organization'
    assert person.organization.name == 'УралГУФК, Челябинск', 'Organization name error'
    assert person.get_year() == 1995, 'Year error'
    assert person.card_number == 1005404, 'Card number error'
    assert person.comment == 'C:123', 'Comment error'
    assert person.qual == Qualification.MS, 'Qualification error'
