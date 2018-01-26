import unittest

from sportorg.models.memory import race, Result, Person, SportidentCard, Group, Course, Organization


class TestMemoryData(unittest.TestCase):
    @staticmethod
    def class_not_equal_msg(obj, t):
        return '{} not is {}'.format(obj.__class__.__name__, t.__class__.__name__)

    def result_equal(self, result):
        self.assertIsInstance(result, Result, self.class_not_equal_msg(result, Result))
        if result.is_sportident() and result.sportident_card is not None:
            self.sportident_card_equal(result.sportident_card)

    def person_equal(self, person):
        self.assertIsInstance(person, Person, self.class_not_equal_msg(person, Person))
        if person.sportident_card is not None:
            self.sportident_card_equal(person.sportident_card)

    def group_equal(self, group):
        self.assertIsInstance(group, Group, self.class_not_equal_msg(group, Group))

    def course_equal(self, course):
        self.assertIsInstance(course, Course, self.class_not_equal_msg(course, Course))

    def organization_equal(self, organization):
        self.assertIsInstance(organization, Organization, self.class_not_equal_msg(organization, Organization))

    def sportident_card_equal(self, card):
        self.assertIsInstance(card, SportidentCard, self.class_not_equal_msg(card, SportidentCard))

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
        for card in obj.sportident_cards:
            self.sportident_card_equal(card)
