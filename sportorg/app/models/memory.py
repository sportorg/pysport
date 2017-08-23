import traceback

from PyQt5.QtWidgets import QMessageBox

from sportorg.language import _
from sportorg.core.model import Model


class Country(Model):
    name = None
    code2 = None
    code3 = None
    digital_code = None
    code = None


class ResultStatus(object):
    OK = "OK"
    FINISHED = "Finished"
    MISSING_PUNCH = "MissingPunch"
    DISQUALIFIED = "Disqualified"
    DID_NOT_FINISH = "DidNotFinish"
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    OVERTIME = "OverTime"
    SPORTING_WITHDRAWAL = "SportingWithdrawal"
    NOT_COMPETING = "NotCompeting"
    MOVED = "Moved"
    MOVED_UP = "MovedUp"
    DID_NOT_START = "DidNotStart"
    DID_NOT_ENTER = "DidNotEnter"
    CANCELLED = "Cancelled"


class CompetitionType(object):
    PREDETERMINED = 'Predetermined'
    SELECTION = 'Selection'
    MARKING = 'Marking'


class Address(Model):
    care_of = None
    street = None
    zip_code = None
    city = None
    state = None
    country = Country()


class Contact(Model):
    name = None
    value = None


class Organization(Model):
    name = None
    address = Address()
    contact = Contact()
    country = Country()
    city = None
    region = None

    count_person = 0


class OrganizationList(list):
    pass


class CourseControl(Model):
    code = None
    length = None
    order = None

    def __eq__(self, other):
        return self.code == other.code


class CourseControlList(list):
    pass


class Course(Model):
    name = None
    type = None
    bib = None
    length = None
    climb = None
    controls = CourseControlList()
    count_person = 0
    count_group = 0

    def get_code_list(self):
        ret = []
        for i in self.controls:
            assert isinstance(i, CourseControl)
            ret.append(str(i.code))
        return ret

    def __eq__(self, other):
        if len(self.controls) != len(other.controls):
            return False
        for i in range(len(self.controls)):
            if self.controls[i] != other.controls[i]:
                return False

        return True


class CourseList(list):
    pass


class Group(Model):
    name = None
    course = Course()
    price = None
    long_name = None
    sex = None

    min_age = None
    max_age = None

    max_time = None  # datetime
    qual_assign_text = None
    start_interval = None
    start_corridor = None
    order_in_corridor = None

    first_number = None
    count_person = 0


class GroupList(list):
    pass


class Result(Model):
    card_number = None
    start_time = None
    finish_time = None
    punches = []
    penalty_time = None  # time of penalties (marked route, false start)
    penalty_laps = None  # count of penalty legs (marked route)
    status = None
    result = None  # time in seconds * 100 (int)
    place = None

    person = None  # reverse link to person

    def __eq__(self, other):
        eq = self.card_number == other.card_number
        eq = eq and self.start_time == other.start_time
        eq = eq and self.finish_time == other.finish_time
        eq = eq and self.punches == other.punches
        return eq

    def __gt__(self, other):
        if self.status is not None and other.status is not None:
            if self.status == ResultStatus.OK and other.status != ResultStatus.OK:
                return True
        return self.result > other.result

    def get_result(self):
        if self.status != 0 and self.status != ResultStatus.OK:
            return None
        return str(self.finish_time - self.start_time)

    def get_result_for_sort(self):
        ret = 0
        if self.status != 0 and self.status != ResultStatus.OK:
            ret += 24*3600*100

        delta = self.finish_time - self.start_time
        ret += delta.seconds * 100
        return ret


class ResultList(list):
    pass


class Person(Model):
    name = None
    surname = None
    sex = None

    card_number = None
    bib = None
    result = Result()

    year = None  # sometime we have only year of birth
    birth_date = None  # datetime
    organization = None
    group = None
    nationality = Country()
    address = Address()
    contact = [Contact()]
    world_code = None  # WRE ID for orienteering and the same
    national_code = None
    rank = None  # position/scores in word ranking
    qual = None  # qualification, used in Russia only
    is_out_of_competition = False  # e.g. 20-years old person, running in M12
    comment = None

    start_time = None
    start_group = 0

class PersonList(list):
    pass


class RaceData(Model):
    name = None
    organisation = None
    start_time = None
    end_time = None
    live_url = None


class Race(Model):
    def __init__(self):
        self.data = RaceData()
        self.courses = []
        self.groups = []
        self.persons = []
        self.results = []
        self.organizations = []
        self.settings = {}

    def set_setting(self, setting, value):
        self.settings[setting] = value

    def get_setting(self, setting):
        if setting in self.settings:
            return self.settings[setting]
        else:
            return ''

    def delete_persons(self, indexes, table):
        try:
            indexes = sorted(indexes, reverse=True)
            for i in indexes:
                self.persons.pop(i)
        except:
            traceback.print_exc()

    def delete_results(self, indexes, table):
        try:
            indexes = sorted(indexes, reverse=True)
            for i in indexes:
                self.results.remove(self.results[i])

        except:
            traceback.print_exc()

    def delete_groups(self, indexes, table):
        try:
            race().update_counters()
            for i in indexes:
                group = self.groups[i]
                if group.count_person > 0:
                    QMessageBox.question(table,
                                         _('Abort'),
                                         _('Cannot remove group') + ' ' + group.name)
                    return False

            indexes = sorted(indexes, reverse=True)
            for i in indexes:
                self.groups.remove(self.groups[i])

        except:
            traceback.print_exc()
            return False
        return True

    def delete_courses(self, indexes, table):
        try:
            race().update_counters()
            for i in indexes:
                course = self.courses[i]
                if course.count_group > 0:
                    QMessageBox.question(table,
                                         _('Abort'),
                                         _('Cannot remove course') + ' ' + course.name)
                    return False

            indexes = sorted(indexes, reverse=True)

            for i in indexes:
                self.courses.remove(self.courses[i])

        except:
            traceback.print_exc()
            return False
        return True

    def delete_organizations(self, indexes, table):
        try:
            race().update_counters()
            for i in indexes:
                organization = self.organizations[i]
                if organization.count_person > 0:
                    QMessageBox.question(table,
                                         _('Abort'),
                                         _('Cannot remove organization') + ' ' + organization.name)
                    return False
            indexes = sorted(indexes, reverse=True)

            for i in indexes:
                self.organizations.remove(self.organizations[i])

        except:
            traceback.print_exc()
            return False
        return True

    def add_new_person(self):
        new_person = Person()
        new_person.name = '_new'
        race().persons.insert(0, new_person)

    def add_new_group(self):
        new_group = Group()
        new_group.name = '_new'
        race().groups.insert(0, new_group)

    def add_new_course(self):
        new_course = Course()
        new_course.name = '_new'
        race().courses.insert(0, new_course)

    def add_new_organization(self):
        new_organization = Organization()
        new_organization.name = '_new'
        race().organizations.insert(0, new_organization)

    def update_counters(self):
        # recalculate group counters
        for i in self.groups:
            i.count_person = 0

        for i in self.persons:
            assert isinstance(i, Person)
            if i.group is not None:
                i.group.count_person += 1

        # recalculate course counters
        for i in self.courses:
            i.count_person = 0
            i.count_group = 0

        for i in self.groups:
            assert isinstance(i, Group)
            if i.course is not None:
                i.course.count_person += i.count_person
                i.course.count_group += 1

        # recalculate team counters
        for i in self.organizations:
            i.count_person = 0

        for i in self.persons:
            assert isinstance(i, Person)
            if i.organization is not None:
                i.organization.count_person += 1

    def get_persons_by_group(self, group):
        return find(self.persons, group=group, return_all=True)

def create(obj, **kwargs):
    return obj.create(**kwargs)


def update(obj, **kwargs):
    obj.update(**kwargs)


def find(iterable: list, **kwargs):
    if len(kwargs.items()) == 0:
        return None
    return_all = kwargs.pop('return_all', False)
    results = []
    for item in iterable:
        f = True
        for key, value in kwargs.items():
            if getattr(item, key) != value:
                f = False
        if f:
            if return_all:
                results.append(item)
            else:
                return item
    if len(results):
        return results
    else:
        return None

event = [create(Race)]


def race(day=None):
    if day is None:
        # TODO: from settings
        day = 0
    else:
        day -= 1

    if day < len(event):
        return event[day]
    else:
        return Race()
