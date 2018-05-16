import unittest

from sportorg.models.memory import race, Result, Person, Group, Course, Organization


class TestMemoryData(unittest.TestCase):
    def setUp(self):
        print('=========>', self.__class__.__name__, self._testMethodName)

    @staticmethod
    def class_not_equal_msg(obj, t):
        return '{} not is {}'.format(obj.__class__.__name__, t.__class__.__name__)

    def result_equal(self, result):
        self.assertIsInstance(result, Result, self.class_not_equal_msg(result, Result))
        self.card_number_equal(result.card_number)

    def person_equal(self, person):
        self.assertIsInstance(person, Person, self.class_not_equal_msg(person, Person))
        if person.card_number:
            self.card_number_equal(person.card_number)

    def group_equal(self, group):
        self.assertIsInstance(group, Group, self.class_not_equal_msg(group, Group))

    def course_equal(self, course):
        self.assertIsInstance(course, Course, self.class_not_equal_msg(course, Course))

    def organization_equal(self, organization):
        self.assertIsInstance(organization, Organization, self.class_not_equal_msg(organization, Organization))

    def card_number_equal(self, card):
        self.assertIsInstance(card, int, self.class_not_equal_msg(card, int))

    def test_main(self):
        obj = race()
        for result in obj.results:
            self.result_equal(result)
        for person in obj.persons:
            self.person_equal(person)
        for group in obj.groups:
            self.group_equal(group)
        for course in obj.courses:
            self.course_equal(course)
        for organization in obj.organizations:
            self.organization_equal(organization)
