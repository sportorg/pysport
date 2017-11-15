import logging

import datetime
from enum import IntEnum, Enum

from PyQt5.QtWidgets import QMessageBox

from sportorg.app.modules.utils.utils import time_remove_day, int_to_time, time_to_hhmmss, time_to_sec
from sportorg.core.otime import OTime
from sportorg.language import _
from sportorg.core.model import Model


class SystemType(Enum):
    MANUAL = 1
    SPORTIDENT = 2
    ALT = 3
    SFR = 4

    def __str__(self):
        return "%s" % self._name_

    def __repr__(self):
        return self.__str__()


class Sex(Enum):
    MF = 0
    M = 1
    F = 2

    def __str__(self):
        return "%s" % self._name_

    def __repr__(self):
        return self.__str__()

    def get_title(self):
        return _(self.name)

    @staticmethod
    def get_by_title(title):
        sex_reverse = {
            _(str(Sex.M)): Sex.M,
            _(str(Sex.F)): Sex.F,
        }
        if title in sex_reverse:
            return sex_reverse[title]
        return Sex.MF

class ResultStatus(Enum):
    NONE = 0
    OK = 1
    FINISHED = 2
    MISSING_PUNCH = 3
    DISQUALIFIED = 4
    DID_NOT_FINISH = 5
    ACTIVE = 6
    INACTIVE = 7
    OVERTIME = 8
    SPORTING_WITHDRAWAL = 9
    NOT_COMPETING = 10
    MOVED = 11
    MOVED_UP = 12
    DID_NOT_START = 13
    DID_NOT_ENTER = 14
    CANCELLED = 15

    def __str__(self):
        return "%s" % self._name_

    def __repr__(self):
        return self.__str__()

    def get_title(self):
        return _(self.name)


class CompetitionType(Enum):
    PREDETERMINED = 1
    SELECTION = 2
    MARKING = 3

    def __str__(self):
        return "%s" % self._name_

    def __repr__(self):
        return self.__str__()


class Country(Model):
    def __init__(self):
        self.name = ''
        self.code2 = ''
        self.code3 = ''
        self.digital_code = ''
        self.code = ''


class Address(Model):
    def __init__(self):
        self.care_of = ''
        self.street = ''
        self.zip_code = ''
        self.city = ''
        self.state = ''
        self.country = Country()


class Contact(Model):
    def __init__(self):
        self.name = ''
        self.value = ''


class Organization(Model):
    def __init__(self):
        self.name = ''
        self.address = Address()
        self.contact = Contact()
        self.country = Country()
        self.city = ''
        self.region = ''
        self.count_person = 0


class CourseControl(Model):
    def __init__(self):
        self.code = ''
        self.length = 0
        self.order = 0

    def __eq__(self, other):
        return self.code == other.code


class Course(Model):
    def __init__(self):
        self.name = ''
        self.type = ''
        self.bib = 0
        self.length = 0
        self.climb = 0
        self.controls = []  # type: List[CourseControl]
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
        self.name = ''
        self.course = Course()
        self.price = 0
        self.long_name = ''
        self.sex = Sex.MF

        self.min_age = 0
        self.max_age = 0

        self.max_time = None  # datetime
        self.qual_assign_text = ''
        self.start_interval = None
        self.start_corridor = 0
        self.order_in_corridor = 0

        self.first_number = 0
        self.count_person = 0
        self.count_finished = 0

        self.ranking = Ranking()

    def get_count_finished(self):
        return self.count_finished

    def get_count_all(self):
        return self.count_person


class Result(Model):
    def __init__(self):
        self.type = None  # type: SystemType
        self.card_number = 0
        self.start_time = None
        self.finish_time = None
        self.punches = []
        self.penalty_time = None  # time of penalties (marked route, false start)
        self.penalty_laps = None  # count of penalty legs (marked route)
        self.status = ResultStatus.OK
        self.result = None  # time in seconds * 100 (int)
        self.place = 0

        self.person = None  # type: Person reverse link to person
        self.assigned_rank = Qualification.NOT_QUALIFIED  # type: Qualification assigned rank (Russia only)

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
        if self.status == ResultStatus.OK and other.status != ResultStatus.OK:
            return False

        if not self.result:
            return True
        if not other.result:
            return False

        return self.result > other.result

    def get_result(self):
        if self.status != ResultStatus.OK:
            return self.status.get_title()

        if not self.person:
            return ''

        return time_to_hhmmss(self.get_finish_time() - self.get_start_time())

    def get_result_for_sort(self):
        ret = 0
        if self.status != 0 and self.status != ResultStatus.OK:
            ret += 24 * 3600 * 100

        delta = self.get_finish_time() - self.get_start_time()
        ret += delta.seconds * 100
        return ret

    def get_result_otime(self):
        return OTime(msec=self.get_result_for_sort()*10)

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
        self.name = ''
        self.surname = ''
        self.sex = Sex.MF

        self.card_number = 0
        self.bib = 0
        self.result = None  # type: Result
        self.results = []  # type: List[Result]

        self.year = 0  # sometime we have only year of birth
        self.birth_date = None  # datetime
        self.organization = None  # type: Organization
        self.group = None  # type: Group
        self.nationality = None  # type: Country
        self.address = None  # type: Address
        self.contact = []  # type: List[Contact]
        self.world_code = None  # WRE ID for orienteering and the same
        self.national_code = None
        self.rank = None  # position/scores in word ranking
        self.qual = Qualification.NOT_QUALIFIED  # type: Qualification 'qualification, used in Russia only'
        self.is_out_of_competition = False  # e.g. 20-years old person, running in M12
        self.comment = ''

        self.start_time = None
        self.start_group = 0

    def add_result(self, result):
        assert isinstance(result, Result)
        add = True
        for r in self.results:
            if r is Result:
                add = False
                break
        if add:
            self.results.append(result)

    @property
    def full_name(self):
        def xstr(s):
            return '' if s is None else str(s)

        return '{} {}'.format(xstr(self.surname), xstr(self.name))


class RaceData(Model):
    def __init__(self):
        self.name = ''
        self.organisation = None
        self.start_time = None
        self.end_time = None
        self.url = ''


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
        new_result.type = SystemType.MANUAL
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

    def add_result(self, result):
        assert isinstance(result, Result)
        add = True
        for r in self.results:
            if r is Result:
                add = False
                break
        if add:
            self.results.insert(0, result)


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


class Qualification(IntEnum):
    NOT_QUALIFIED = 0
    I_Y = 1
    II_Y = 2
    III_Y = 3
    I = 4
    II = 5
    III = 6
    KMS = 7
    MS = 8
    MSMK = 9
    ZMS = 10

    @staticmethod
    def get_qual_by_code(code):
        return Qualification(code)

    @staticmethod
    def get_qual_by_name(name):
        qual_reverse = {
            '': 0,
            ' ': 0,
            'б/р': 0,
            'IIIю': 3,
            'IIю': 2,
            'Iю': 1,
            'III': 6,
            'II': 5,
            'I': 4,
            'КМС': 7,
            'МС': 8,
            'МСМК': 9,
            'ЗМС': 10
        }
        return Qualification(qual_reverse[name])

    def get_title(self):
        qual = {
            '': 'б/р',
            0: 'б/р',
            3: 'IIIю',
            2: 'IIю',
            1: 'Iю',
            6: 'III',
            5: 'II',
            4: 'I',
            7: 'КМС',
            8: 'МС',
            9: 'МСМК',
            10: 'ЗМС'
        }
        return qual[self.value]

    # see https://www.minsport.gov.ru/sportorentir.xls - Russian orienteering only!
    def get_scores(self):
        scores = {
            '': 0,
            0: 0,
            3: 1,
            2: 2,
            1: 3,
            6: 6,
            5: 25,
            4: 50,
            7: 80,
            8: 100,
            9: 100,
            10: 100
        }
        return scores[self.value]


class RankingItem(object):
    def __init__(self, qual=Qualification.NOT_QUALIFIED, use_scores=True, max_place=0, max_time=None, is_active=True):
        self.qual = qual
        self.use_scores = use_scores
        self.max_place = max_place
        self.max_time = max_time
        self.is_active = is_active
        self.percent = 0

    def get_json_data(self):
        ret = {}
        ret['qual'] = self.qual.get_title()
        ret['max_place'] = self.max_place
        ret['max_time'] = time_to_hhmmss(self.max_time)
        ret['percent'] = self.percent
        return ret


class Ranking(object):
    def __init__(self):
        self.is_active = False
        self.rank_scores = 0
        self.rank = {}
        self.rank[Qualification.MS] = RankingItem(qual=Qualification.MS, use_scores=False, max_place=2, is_active=False)
        self.rank[Qualification.KMS] = RankingItem(qual=Qualification.KMS, use_scores=False, max_place=6, is_active=False)
        self.rank[Qualification.I] = RankingItem(qual=Qualification.I)
        self.rank[Qualification.II] = RankingItem(qual=Qualification.II)
        self.rank[Qualification.III] = RankingItem(qual=Qualification.III)
        self.rank[Qualification.I_Y] = RankingItem(qual=Qualification.I_Y, is_active=False)
        self.rank[Qualification.II_Y] = RankingItem(qual=Qualification.II_Y, is_active=False)
        self.rank[Qualification.III_Y] = RankingItem(qual=Qualification.III_Y, is_active=False)

    def get_max_qual(self):
        max_qual = Qualification.NOT_QUALIFIED
        for i in self.rank.values():
            assert isinstance(i, RankingItem)
            if i.is_active:
                if i.max_place or (i.max_time and i.max_time.to_msec() > 0):
                    if max_qual.get_scores() < i.qual.get_scores():
                        max_qual = i.qual
        return max_qual

    def get_json_data(self):
        ret = {}
        ret['is_active'] = self.is_active
        if self.is_active:
            ret['rank_scores'] = self.rank_scores
            ret['max_qual'] = self.get_max_qual().get_title()
            rank_array = []

            for i in self.rank.values():
                if i.is_active:
                    if i.max_place or (i.max_time and i.max_time.to_msec() > 0):
                        rank_array.append(i.get_json_data())

            ret['rank'] = rank_array
        return ret


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
