import unittest

from sportorg.models.memory import race, Person, Group, find, Qualification, Organization
from sportorg.modules.winorient import winorient


class TestWinorient(unittest.TestCase):
    def setUp(self):
        print('=========>', self.__class__.__name__, self._testMethodName)

    def test_import_csv(self):
        winorient.import_csv('test/5979_csv_wo.csv')
        person = find(race().persons, name='Сергей', surname='Добрынин')
        self.assertIsInstance(person, Person, 'Not person')
        self.assertIsInstance(person.group, Group, 'Not group')
        self.assertEqual(person.group.name, 'МУЖЧИНЫ', 'Group name error')
        self.assertIsInstance(person.organization, Organization, 'Not organization')
        self.assertEqual(person.organization.name, 'УралГУФК, Челябинск', 'Organization name error')
        self.assertEqual(person.get_year(), 1995, 'Year error')
        self.assertEqual(person.sportident_card, 1005404, 'Card number error')
        self.assertEqual(person.comment, 'C:123', 'Comment error')
        self.assertEqual(person.qual, Qualification.MS, 'Qualification error')
