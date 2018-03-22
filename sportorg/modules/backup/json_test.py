import logging
import unittest

from sportorg.models.memory import race, Person, Group, Organization
from sportorg.modules.backup.file import File


class TestJson(unittest.TestCase):
    def setUp(self):
        print('=========>', self.__class__.__name__, self._testMethodName)

    def test_main(self):
        File('test/test.json', logging.root, File.JSON).open()
        r = race()
        person = None
        for p in r.persons:
            if p.full_name == 'Akhtarov Danil' and p.sportident_card == 9777775:
                person = p
        self.assertIsInstance(person, Person, 'Import person failed')
        self.assertIsInstance(person.group, Group, 'Import group failed')
        self.assertIsInstance(person.organization, Organization, 'Import organization failed')
