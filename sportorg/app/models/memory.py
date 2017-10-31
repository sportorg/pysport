import logging

import datetime
from PyQt5.QtWidgets import QMessageBox

from sportorg.app.modules.utils.utils import time_remove_day, int_to_time, time_to_hhmmss, time_to_sec
from sportorg.language import _
from sportorg.core.model import Model


class Country(Model):
    def __init__(self):
        self.name = None
        self.code2 = None
        self.code3 = None
        self.digital_code = None
        self.code = None


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
    def __init__(self):
        self.care_of = None
        self.street = None
        self.zip_code = None
        self.city = None
        self.state = None
        self.country = Country()


class Contact(Model):
    def __init__(self):
        self.name = None
        self.value = None


class Organization(Model):
    def __init__(self):
        self.name = None
        self.address = Address()
        self.contact = Contact()
        self.country = Country()
        self.city = None
        self.region = None
        self.count_person = 0


class CourseControl(Model):
    def __init__(self):
        self.code = None
        self.length = None
        self.order = None

    def __eq__(self, other):
        return self.code == other.code


class Course(Model):
    def __init__(self):
        self.name = ''
        self.type = ''
        self.bib = 0
        self.length = 0
        self.climb = 0
        self.controls = [] # type: List[CourseControl]
        self.count_person = 0
        self.count_group = 0
        self.corridor = 0

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


class Group(Model):
    def __init__(self):
        self.name = None
        self.course = Course()
        self.price = None
        self.long_name = None
        self.sex = None

        self.min_age = None
        self.max_age = None

        self.max_time = None  # datetime
        self.qual_assign_text = None
        self.start_interval = None
        self.start_corridor = 0
        self.order_in_corridor = 0

        self.first_number = None
        self.count_person = 0
        self.count_finished = 0

    def get_count_finished(self):
        return self.count_finished

    def get_count_all(self):
        return self.count_person


class Result(Model):
    def __init__(self):
        self.card_number = None
        self.start_time = None
        self.finish_time = None
        self.punches = []
        self.penalty_time = None  # time of penalties (marked route, false start)
        self.penalty_laps = None  # count of penalty legs (marked route)
        self.status = ResultStatus.OK
        self.result = None  # time in seconds * 100 (int)
        self.place = None

        self.person = None  # type: Person reverse link to person

    def __repr__(self):
        punches = ''
        for punch in self.punches:
            punches += '{} — {}\n'.format(punch[0], punch[1])
        person = self.person.full_name if self.person is not None else ''
        return """
Card number: {}
Start: {}
Finish: {}
Person: {}
Punches:
{}""".format(self.card_number, self.start_time, self.finish_time, person, punches)

    def __eq__(self, other):
        eq = self.card_number == other.card_number
        if self.start_time and other.start_time:
            eq = eq and time_to_sec(self.start_time) == time_to_sec(other.start_time)
        if self.finish_time and other.finish_time:
            eq = eq and time_to_sec(self.finish_time) == time_to_sec(other.finish_time)
        if len(self.punches) == len(other.punches):
            for i in range(len(self.punches)):
                eq = eq and self.punches[i][0] == other.punches[i][0] and time_to_sec(self.punches[i][1]) == time_to_sec(other.punches[i][1])
        else:
            return False
        return eq

    def __gt__(self, other):
        if self.status is not None and other.status is not None:
            if self.status == ResultStatus.OK and other.status != ResultStatus.OK:
                return False
        return self.result > other.result

    def get_result(self):
        if self.status != 0 and self.status != ResultStatus.OK:
            return None

        if not self.person:
            return None

        return time_to_hhmmss(self.get_finish_time() - self.get_start_time())

    def get_result_for_sort(self):
        ret = 0
        if self.status != 0 and self.status != ResultStatus.OK:
            ret += 24 * 3600 * 100

        delta = self.get_finish_time() - self.get_start_time()
        ret += delta.seconds * 100
        return ret

    def get_start_time(self):
        obj = race()
        start_source = obj.get_setting('sportident_start_source', 'protocol')
        if start_source == 'protocol':
            if self.person:
                return time_remove_day(self.person.start_time)
        elif start_source == 'station':
            return time_remove_day(self.start_time)
        elif start_source == 'cp':
            pass
        elif start_source == 'gate':
            pass

        return int_to_time(0)

    def get_finish_time(self):
        obj = race()
        finish_source = obj.get_setting('sportident_finish_source', 'station')
        if finish_source == 'station':
            if self.finish_time:
                return time_remove_day(self.finish_time)
        elif finish_source == 'cp':
            pass
        elif finish_source == 'beam':
            pass

        return datetime.datetime.now()


class Person(Model):
    def __init__(self):
        self.name = None
        self.surname = None
        self.sex = None

        self.card_number = None
        self.bib = 0
        self.result = None  # type: Result
        self.results = {}  # type: Dict[str, Result]

        self.year = None  # sometime we have only year of birth
        self.birth_date = None  # datetime
        self.organization = None  # type: Organization
        self.group = None  # type: Group
        self.nationality = None  # type: Country
        self.address = None  # type: Address
        self.contact = []  # type: List[Contact]
        self.world_code = None  # WRE ID for orienteering and the same
        self.national_code = None
        self.rank = None  # position/scores in word ranking
        self.qual = None  # type: str 'qualification, used in Russia only'
        self.is_out_of_competition = False  # e.g. 20-years old person, running in M12
        self.comment = None

        self.start_time = None
        self.start_group = 0

    @property
    def full_name(self):
        def xstr(s):
            return '' if s is None else str(s)

        return '{} {}'.format(xstr(self.surname), xstr(self.name))


class RaceData(Model):
    def __init__(self):
        self.name = None
        self.organisation = None
        self.start_time = None
        self.end_time = None
        self.live_url = None


class Race(Model):
    def __init__(self):
        self.data = RaceData()
        self.courses = []  # type: List[Course]
        self.groups = []  # type: List[Group]
        self.persons = []  # type: List[Person]
        self.results = []  # type: List[Result]
        self.organizations = []  # type: List[Organization]
        self.settings = {}

    def set_setting(self, setting, value):
        self.settings[setting] = value

    def get_setting(self, setting, nvl_value=''):
        if setting in self.settings:
            return self.settings[setting]
        else:
            return nvl_value

    def delete_persons(self, indexes, table):
        try:
            indexes = sorted(indexes, reverse=True)
            for i in indexes:
                del self.persons[i]
        except Exception as e:
            logging.exception(str(e))

    def delete_results(self, indexes, table):
        try:
            indexes = sorted(indexes, reverse=True)
            for i in indexes:
                del self.results[i]

        except Exception as e:
            logging.exception(str(e))

    def delete_groups(self, indexes, table):
        try:
            race().update_counters()
            for i in indexes:
                group = self.groups[i]  # type: Group
                if group.count_person > 0:
                    QMessageBox.question(table,
                                         _('Error'),
                                         _('Cannot remove group') + ' ' + group.name)
                    return False

            indexes = sorted(indexes, reverse=True)
            for i in indexes:
                del self.groups[i]

        except Exception as e:
            logging.exception(str(e))
            return False
        return True

    def delete_courses(self, indexes, table):
        try:
            race().update_counters()
            for i in indexes:
                course = self.courses[i]  # type: Course
                if course.count_group > 0:
                    QMessageBox.question(table,
                                         _('Error'),
                                         _('Cannot remove course') + ' ' + course.name)
                    return False

            indexes = sorted(indexes, reverse=True)

            for i in indexes:
                del self.courses[i]

        except Exception as e:
            logging.exception(str(e))
            return False
        return True

    def delete_organizations(self, indexes, table):
        try:
            race().update_counters()
            for i in indexes:
                organization = self.organizations[i]  # type: Organization
                if organization.count_person > 0:
                    QMessageBox.question(table,
                                         _('Error'),
                                         _('Cannot remove organization') + ' ' + organization.name)
                    return False
            indexes = sorted(indexes, reverse=True)

            for i in indexes:
                del self.organizations[i]

        except Exception as e:
            logging.exception(str(e))
            return False
        return True

    def add_new_person(self):
        new_person = Person()
        new_person.name = '_new'
        race().persons.insert(0, new_person)

    def add_new_result(self):
        new_result = Result()
        new_result.finish_time = datetime.datetime.now()
        race().results.insert(0, new_result)

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

    def get_persons_by_corridor(self, corridor):
        obj = race()
        ret = []
        for person in obj.persons:
            if person.group:
                if person.group.start_corridor == corridor:
                    ret.append(person)
        return ret


class Config(object):
    _configurations = {
        'autosave': False,
        'autoconnect': False,
        'open_recent_file': False,
    }

    @classmethod
    def set(cls, config, value):
        cls._configurations[config] = value

    @classmethod
    def get(cls, config, nvl_value=None):
        if config in cls._configurations:
            return cls._configurations[config]
        else:
            return nvl_value

    @classmethod
    def get_all(cls):
        return cls._configurations

    @classmethod
    def set_parse(cls, option, param):
        def is_bool(val):
            return val in ['True', 'False', '0', '1', True, False, 0, 1, 'true', 'false']

        def is_int(s):
            try:
                int(s)
                return True
            except ValueError:
                return False

        def is_float(s):
            try:
                float(s)
                return True
            except ValueError:
                return False
        if is_bool(param):
            param = param in ['True', '1', True, 1, 'true']
        elif is_int(param):
            param = int(param)
        elif is_float(param):
            param = float(param)
        cls.set(option, param)


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
