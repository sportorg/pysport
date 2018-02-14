import uuid
from abc import abstractmethod
from enum import IntEnum, Enum
from typing import Dict, List, Any, Union

import datetime

from sportorg.core.model import Model
from sportorg.core.otime import OTime
from sportorg.language import _
from sportorg.utils.time import int_to_otime, time_to_hhmmss, time_to_sec


class NotEmptyException(Exception):
    pass


class Limit:
    BIB = 10000
    PRICE = 100000000


class SystemType(Enum):
    NONE = 0
    MANUAL = 1
    SPORTIDENT = 2

    def __str__(self):
        return "%s" % self._name_

    def __repr__(self):
        return self.__str__()


class _TitleType(Enum):

    def __str__(self):
        return "%s" % self._name_

    def __repr__(self):
        return self.__str__()

    def get_title(self):
        return _(self.__str__())

    @classmethod
    def get_titles(cls):
        ret = [obj.get_title() for obj in cls]
        return ret


class Sex(_TitleType):
    MF = 0
    M = 1
    F = 2


class RaceType(_TitleType):
    INDIVIDUAL_RACE = 0
    MASS_START = 1
    PURSUIT = 2
    RELAY = 3
    ONE_MAN_RELAY = 4
    SPRINT_RELAY = 5


class ResultStatus(_TitleType):
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


class Country(Model):
    def __init__(self):
        self.name = ''
        self.code2 = ''
        self.code3 = ''
        self.digital_code = ''
        self.code = ''

    def __repr__(self):
        return self.name


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

    def __repr__(self):
        return '{} {}'.format(self.name, self.value)


class Organization(Model):
    def __init__(self):
        self.id = uuid.uuid4()
        self.name = ''
        self.address = Address()
        self.contact = Contact()
        self.count_person = 0

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'Organization {}'.format(self.name)

    def to_dict(self):
        return {
            'name': self.name
        }


class CourseControl(Model):
    def __init__(self):
        self.code = ''
        self.length = 0
        self.order = 0

    def __str__(self):
        return '{} {}'.format(self.code, self.length)   

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.code == other.code

    def get_int_code(self):
        """ Get int code
        31 933 -> 31
        31(31,32,33) 933 -> 31
        * -> 0
        % -> 0
        """
        if not self.code:
            return 0

        if isinstance(self.code, int):
            return self.code

        tmp = str(self.code)
        char = tmp[0]
        if char == '*' or char == '%':
            return 0
        res = ''

        index = 0
        while char.isdigit() and index <= len(tmp) - 1:
            res += char
            index += 1
            if index < len(tmp):
                char = tmp[index]
        return int(res)

    def to_dict(self):
        return {
            'code': self.code,
            'length': self.length
        }


class CoursePart(Model):
    def __init__(self):
        self.controls = []  # type: List[CourseControl]
        self.control_count = 0
        self.is_free = False


class Course(Model):
    def __init__(self):
        self.id = uuid.uuid4()
        self.name = ''
        self.bib = 0
        self.length = 0
        self.climb = 0
        self.controls = []  # type: List[CourseControl]

        self.count_person = 0
        self.count_group = 0
        self.corridor = 0

    def __repr__(self):
        return 'Course {}'.format(self.name)

    def __eq__(self, other):
        if len(self.controls) != len(other.controls):
            return False
        for i in range(len(self.controls)):
            if self.controls[i] != other.controls[i]:
                return False

        return True

    def is_unknown(self):
        for control in self.controls:
            if '*' in control.code or '%' in control.code:
                return True

        return False

    def get_code_list(self):
        ret = []
        for i in self.controls:
            assert isinstance(i, CourseControl)
            ret.append(str(i.code))
        return ret

    def to_dict(self):
        return {
            'name': self.name,
            'length': self.length,
            'climb': self.climb,
            'corridor': self.corridor
        }


class Group(Model):
    def __init__(self):
        self.id = uuid.uuid4()
        self.name = ''
        self.course = None  # type: Course
        self.price = 0
        self.long_name = ''
        self.sex = Sex.MF

        self.min_age = 0
        self.max_age = 0

        self.max_time = OTime()
        self.qual_assign_text = ''
        self.start_interval = OTime()
        self.start_corridor = 0
        self.order_in_corridor = 0

        self.first_number = 0
        self.count_person = 0
        self.count_finished = 0

        self.ranking = Ranking()
        self.__type = None  # type: RaceType
        self.relay_legs = 0

    def __repr__(self):
        return 'Group {}'.format(self.name)

    def get_count_finished(self):
        return self.count_finished

    def get_count_all(self):
        return self.count_person

    def get_type(self):
        if self.__type:
            return self.__type

    def set_type(self, new_type):
        self.__type = new_type

    def is_relay(self):
        return self.get_type() == RaceType.RELAY

    def to_dict(self):
        return {
            'name': self.name,
            'long_name': self.long_name,
            'price': self.price,
        }


class SportidentCardModel(Enum):
    NONE = 0
    P_CARD = 1
    SI5 = 2
    SI8 = 3
    SI9 = 4
    SI10 = 5
    SI11 = 6
    SIAC = 7

    def __str__(self):
        return "%s" % self._name_

    def __repr__(self):
        return self.__str__()


class SportidentCard(Model):
    def __init__(self, number=0):
        self.number = number
        self.model = SportidentCardModel.NONE
        self.club = ''
        self.owner = ''
        self.person = None  # type: Person

    def __int__(self):
        return int(self.number)

    def __bool__(self):
        return bool(self.number)

    def __str__(self):
        return str(self.number)

    def __repr__(self):
        return '{} {}'.format(self.model, self.number)

    def __eq__(self, other):
        if other is None:
            return False
        assert isinstance(other, SportidentCard)
        if self.number == 0:
            return False
        return self.number == other.number


class Split(Model):
    def __init__(self):
        self.code = 0  # type: int
        self.time = None  # type: OTime
        self.pace = None  # type: OTime

    def __eq__(self, other):
        assert isinstance(other, Split)
        if self.code == 0 or other.code == 0:
            return False
        if self.time is None or other.time is None:
            return False
        return self.code == other.code and self.time == other.time


class Result:
    def __init__(self):
        if type(self) == Result:
            raise Exception("<Result> must be subclassed.")
        self.id = uuid.uuid4()
        self.start_time = None  # type: OTime
        self.finish_time = None  # type: OTime
        self.result = None  # type: OTime
        self.person = None  # type: Person
        self.status = ResultStatus.OK
        self.penalty_time = None  # type: OTime
        self.penalty_laps = 0  # count of penalty legs (marked route)
        self.place = None  # type: Union[int, str]
        self.scores = 0  # type: int
        self.assigned_rank = Qualification.NOT_QUALIFIED

    def __str__(self):
        return str(self.system_type)

    def __repr__(self):
        return 'Result {} {}'.format(self.system_type, self.status)

    def __eq__(self, other):
        eq = self.system_type and other.system_type
        if self.start_time and other.start_time:
            eq = eq and time_to_sec(self.start_time) == time_to_sec(other.start_time)
        if self.finish_time and other.finish_time:
            eq = eq and time_to_sec(self.finish_time) == time_to_sec(other.finish_time)
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

    @property
    @abstractmethod
    def system_type(self) -> SystemType:
        pass

    def get_result(self):
        if self.status != ResultStatus.OK:
            return self.status.get_title()

        if not self.person:
            return ''

        return time_to_hhmmss(self.get_finish_time() - self.get_start_time() + self.get_penalty_time())

    def get_result_for_sort(self):
        ret = 0
        if self.status != 0 and self.status != ResultStatus.OK:
            ret += 24 * 3600 * 1000

        delta = self.get_finish_time() - self.get_start_time() + self.get_penalty_time()
        ret += delta.to_msec()
        return ret

    def get_result_otime(self):
        return OTime(msec=self.get_result_for_sort())

    def get_start_time(self):
        if self.start_time and self.start_time.to_msec():
            return self.start_time
        if self.person and self.person.start_time and self.person.start_time.to_msec():
            return self.person.start_time
        return int_to_otime(0)

    def get_finish_time(self):
        if self.finish_time:
            return self.finish_time

        return OTime.now()

    def get_penalty_time(self):
        if self.penalty_time:
            return self.penalty_time
        return OTime()

    def get_course_splits(self, course=None):
        return []

    def check(self, course=None):
        return True

    def is_sportident(self):
        return self.system_type == SystemType.SPORTIDENT

    def is_manual(self):
        return self.system_type == SystemType.MANUAL


class ResultManual(Result):
    system_type = SystemType.MANUAL


class ResultSportident(Result):
    system_type = SystemType.SPORTIDENT

    def __init__(self):
        super().__init__()
        self.sportident_card = None  # type: SportidentCard
        self.splits = []  # type: List[Split]
        self.__start_time = None
        self.__finish_time = None

    def __repr__(self):
        splits = ''
        for split in self.splits:
            splits += '{} — {}\n'.format(split[0], split[1])
        person = self.person.full_name if self.person is not None else ''
        return "Card: {}\nStart: {}\nFinish: {}\nPerson: {}\nSplits:\n{}".format(
            self.sportident_card, self.start_time, self.finish_time, person, splits)

    def __eq__(self, other):
        eq = self.sportident_card == other.sportident_card and super().__eq__(other)
        if len(self.splits) == len(other.splits):
            for i in range(len(self.splits)):
                eq = eq and self.splits[i].code == other.splits[i].code
                eq = eq and time_to_sec(self.splits[i].time) == time_to_sec(other.splits[i].time)
        else:
            return False
        return eq

    def get_start_time(self):
        obj = race()
        start_source = obj.get_setting('sportident_start_source', 'protocol')
        if start_source == 'protocol':
            if self.person and self.person.start_time and self.person.start_time.to_msec():
                return self.person.start_time
        elif start_source == 'station':
            if self.start_time and self.start_time.to_msec():
                return self.start_time
            elif self.person and self.person.start_time and self.person.start_time.to_msec():
                return self.person.start_time
        elif start_source == 'cp':
            if self.__start_time is not None:
                return self.__start_time
            if len(self.splits):
                start_cp_number = obj.get_setting('sportident_start_cp_number', 31)
                if start_cp_number == 0:
                    self.__start_time = self.splits[0].time
                    return self.__start_time
                for split in self.splits:
                    if split.code == start_cp_number:
                        self.__start_time = split.time
                        return self.__start_time
        elif start_source == 'gate':
            pass

        return int_to_otime(0)

    def get_finish_time(self):
        obj = race()
        finish_source = obj.get_setting('sportident_finish_source', 'station')
        if finish_source == 'station':
            if self.finish_time:
                return self.finish_time
        elif finish_source == 'cp':
            if self.__finish_time is not None:
                return self.__finish_time
            if len(self.splits):
                finish_cp_number = obj.get_setting('sportident_finish_cp_number', 90)
                if finish_cp_number == -1:
                    self.__finish_time = self.splits[-1].time
                    return self.__finish_time
                for split in reversed(self.splits):
                    if split.code == finish_cp_number:
                        self.__finish_time = split.time
                        return self.__finish_time
        elif finish_source == 'beam':
            pass

        return OTime.now()

    def clear(self):
        self.__start_time = None
        self.__finish_time = None

    def get_course_splits(self, course=None):
        result_splits = []
        for i, split in enumerate(self.splits):
            if not i or split.code != self.splits[i-1].code:
                result_splits.append(split)
        if not course or course.is_unknown():
            return result_splits
        max_len = len(result_splits)
        splits = []
        i = 0
        for control in course.controls:
            if max_len == i:
                break
            if str(result_splits[i].code) in control.code:
                splits.append(result_splits[i])
                i += 1
        return splits

    def check(self, course=None):
        if not course:
            return super().check()
        controls = course.controls
        i = 0
        count_controls = len(controls)
        if count_controls == 0:
            return True

        for split in self.splits:
            try:
                template = str(controls[i].code)
                cur_code = int(split.code)

                list_exists = False
                list_contains = False
                ind_begin = template.find('(')
                ind_end = template.find(')')
                if ind_begin > 0 and ind_end > 0:
                    list_exists = True
                    # any control from the list e.g. '%(31,32,33)'
                    arr = template[ind_begin + 1:ind_end].split(',')
                    if str(cur_code) in arr:
                        list_contains = True

                if template.find('%') > -1:
                    # non-unique control
                    if not list_exists or list_contains:
                        # any control '%' or '%(31,32,33)' or '31%'
                        i += 1

                elif template.find('*') > -1:
                    # unique control '*' or '*(31,32,33)' or '31*'
                    if list_exists and not list_contains:
                        # not in list
                        continue
                    # test previous splits
                    is_unique = True
                    for prev_split in self.splits[0:i]:
                        if int(prev_split.code) == cur_code:
                            is_unique = False
                            break
                    if is_unique:
                        i += 1

                else:
                    # simple pre-ordered control '31 989' or '31(31,32,33) 989'
                    if list_exists:
                        # control with optional codes '31(31,32,33) 989'
                        if list_contains:
                            i += 1
                    else:
                        # just cp '31 989'
                        is_equal = cur_code == int(controls[i].code)
                        if is_equal:
                            i += 1

                if i == count_controls:
                    return True

            except KeyError:
                return False

        return False


class Person(Model):
    def __init__(self):
        self.id = uuid.uuid4()
        self.name = ''
        self.surname = ''
        self.sex = Sex.MF

        self.sportident_card = None  # type: SportidentCard
        self.bib = 0

        self.year = 0  # sometime we have only year of birth
        self.birth_date = None  # type: datetime
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
        self.is_paid = False
        self.is_rented_sportident_card = False
        self.is_personal = False
        self.comment = ''

        self.start_time = None  # type: OTime
        self.start_group = 0

    def __repr__(self):
        return '{} {} {}'.format(self.full_name, self.bib, self.group)

    @property
    def full_name(self):
        surname = self.surname
        if surname:
            surname += ' '
        return '{}{}'.format(surname, self.name)

    def to_dict(self, course=None):
        sportident_card = ''
        if self.sportident_card is not None and int(self.sportident_card):
            sportident_card = str(self.sportident_card)
        course_name = ''
        if self.group is not None and self.group.course is not None:
            course_name = self.group.course.name
        if course:
            course_name = course.name
        return {
            'name': self.full_name,
            'bib': self.bib,
            'course': course_name,
            'team': self.organization.name if self.organization is not None else '',
            'group': self.group.name if self.group is not None else '',
            'group_start_corridor': self.group.start_corridor if self.group is not None else 0,
            'price': self.group.price if self.group is not None else 0,
            'qual': self.qual.get_title(),
            'year': self.year if self.year else '',
            'sportident_card': sportident_card,
            'start': time_to_hhmmss(self.start_time),
            'comment': self.comment,
            'is_out_of_competition': self.is_out_of_competition,
            'is_rented': self.is_rented_sportident_card,
            'is_paid': self.is_paid,
        }


class RaceData(Model):
    def __init__(self):
        self.name = ''
        self.organisation = None  # type: Organization
        self.start_time = None  # type: datetime
        self.end_time = None  # type: datetime
        self.url = ''

    def __repr__(self):
        return '{} {}'.format(self.name, self.start_time)


class Race(Model):
    def __init__(self):
        self.id = uuid.uuid4()
        self.data = RaceData()
        self.courses = []  # type: List[Course]
        self.groups = []  # type: List[Group]
        self.persons = []  # type: List[Person]
        self.results = []  # type: List[Result]
        self.relay_teams = []  # type: List[RelayTeam]
        self.organizations = []  # type: List[Organization]
        self.sportident_cards = []  # type: List[SportidentCard]
        self.settings = {}  # type: Dict[str, Any]

    def __repr__(self):
        return repr(self.data)

    def to_dict(self):
        start_date = self.get_setting('start_date', datetime.datetime.now().replace(second=0, microsecond=0))
        return {
            'title': self.get_setting('main_title', ''),
            'sub_title': self.get_setting('sub_title', ''),
            'url': self.get_setting('url', ''),
            'date': start_date.strftime("%d.%m.%Y")
        }

    def get_type(self, group: Group):
        if group.get_type():
            return group.get_type()
        return self.get_setting('race_type', RaceType.INDIVIDUAL_RACE)

    def set_setting(self, setting, value):
        self.settings[setting] = value

    def get_setting(self, setting, nvl_value=None):
        if setting in self.settings:
            return self.settings[setting]
        else:
            return nvl_value

    def new_sportident_card(self, number=None):
        if number is None:
            number = 0
        if isinstance(number, SportidentCard):
            number = int(number)
        assert isinstance(number, int)
        for card in self.sportident_cards:
            if number == int(card):
                return card
        card = SportidentCard(number)
        self.sportident_cards.append(card)
        return card

    def person_sportident_card(self, person, number=None):
        assert isinstance(person, Person)
        card = self.new_sportident_card(number)
        if card.person is not None:
            card.person.sportident_card = None
            card.person.is_rented_sportident_card = False
        card.person = person
        person.sportident_card = card

        return person

    def delete_persons(self, indexes):
        indexes = sorted(indexes, reverse=True)
        for i in indexes:
            del self.persons[i]

    def delete_results(self, indexes):
        indexes = sorted(indexes, reverse=True)
        for i in indexes:
            del self.results[i]

    def delete_groups(self, indexes):
        self.update_counters()
        for i in indexes:
            group = self.groups[i]  # type: Group
            if group.count_person > 0:
                raise NotEmptyException('Cannot remove group')

        indexes = sorted(indexes, reverse=True)
        for i in indexes:
            del self.groups[i]
        return True

    def delete_courses(self, indexes):
        self.update_counters()
        for i in indexes:
            course = self.courses[i]  # type: Course
            if course.count_group > 0:
                raise NotEmptyException('Cannot remove course')

        indexes = sorted(indexes, reverse=True)

        for i in indexes:
            del self.courses[i]
        return True

    def delete_organizations(self, indexes):
        self.update_counters()
        for i in indexes:
            organization = self.organizations[i]  # type: Organization
            if organization.count_person > 0:
                raise NotEmptyException('Cannot remove organization')
        indexes = sorted(indexes, reverse=True)

        for i in indexes:
            del self.organizations[i]
        return True

    def find_person_result(self, person):
        for i in self.results:
            if i.person is person:
                return i
        return None

    def find_course(self, person):
        # first get course by number
        bib = person.bib
        ret = find(self.courses, name=str(bib))
        if not ret and bib > 1000:
            course_name = '{}.{}'.format(bib % 1000, bib // 1000)
            ret = find(self.courses, name=course_name)
        # usual connection via group
        if not ret and person.group:
            ret = person.group.course
        return ret

    def get_course_splits(self, result):
        """List[Split]"""
        if not result.person:
            return result.get_course_splits()
        course = self.find_course(result.person)  # type: Course
        return result.get_course_splits(course)

    @staticmethod
    def new_result():
        new_result = ResultManual()
        new_result.finish_time = OTime.now()
        return new_result

    @staticmethod
    def new_sportident_result():
        new_result = ResultSportident()
        new_result.finish_time = OTime.now()
        return new_result

    def add_new_person(self):
        new_person = Person()
        self.persons.insert(0, new_person)

    def add_new_group(self):
        new_group = Group()
        self.groups.insert(0, new_group)

    def add_new_course(self):
        new_course = Course()
        self.courses.insert(0, new_course)

    def add_new_organization(self):
        new_organization = Organization()
        self.organizations.insert(0, new_organization)

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
        ret = []
        for person in self.persons:
            if person.group:
                if person.group.start_corridor == corridor:
                    ret.append(person)
        return ret

    def add_new_result(self, result):
        self.results.insert(0, result)

    def add_result(self, result):
        assert isinstance(result, Result)
        add = True
        for r in self.results:
            if r is result:
                add = False
                break
        if add:
            self.add_new_result(result)

    def clear_sportident_results(self):
        for result in self.results:
            if result.is_sportident():
                result.clear()


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
    # http://www.minsport.gov.ru/2017/doc/Sportivnoe-orentirovanie-evsk2021.xls
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

    def get_dict_data(self):
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

    def get_dict_data(self):
        ret = {}
        ret['is_active'] = self.is_active
        if self.is_active:
            ret['rank_scores'] = self.rank_scores
            ret['max_qual'] = self.get_max_qual().get_title()
            rank_array = []

            for i in self.rank.values():
                if i.is_active:
                    if i.max_place or (i.max_time and i.max_time.to_msec() > 0):
                        rank_array.append(i.get_dict_data())

            ret['rank'] = rank_array
        return ret


class RelayLeg(object):
    """
    Describes one leg of relay team
    Has the distribution of relay variant
    example of file to import here - should generate teams and team legs:
    101.1: CB
    101.2: AC
    101.3: BA
    """
    def __init__(self, team):
        self.number = 0
        self.leg = 0
        self.variant = ''
        self.person = None
        self.result = None
        self.course = None  # optional link to the course, prefer to use variant and bib to find course
        self.team = team

    def get_course(self):
        """Get the course to check control order. Try to use bib and variant to find course"""
        bib = self.get_bib()
        course = find(self.team.courses, name=str(bib))
        if course:
            return course

        # get course via group
        person = self.get_person()
        if person and isinstance(person, Person):
            if person.group:
                return person.group.course

        return None

    def get_relay_team(self):
        """:return relay team object"""
        return self.team

    def get_next_leg(self):
        """:return next leg of relay team, None if this leg is last"""
        team = self.get_relay_team()
        if team and isinstance(team, RelayTeam):
            if len(team.legs) > self.leg + 1:
                return team.legs[self.leg + 1]
        return None

    def get_prev_leg(self):
        """:return previous leg of relay team, None if this leg is first"""
        if self.leg > 1:
            team = self.get_relay_team()
            if team and isinstance(team, RelayTeam):
                return team.legs[self.leg - 1]
        return None

    def get_bib(self):
        """:return person bib, e.g. 1.1 or 1001 depending on settings"""
        if self.number < 1000:
            return 1000 * self.leg + self.number
        return "{}.{}".format(self.number, self.leg)

    def get_variant(self):
        """:return person distribution variant e.g. ABCA"""
        return self.variant

    def parse_variant_text(self, text):
        """parse text like '101.1: CB'"""
        arr = str(text).split(':')
        if len(arr) == 2:
            bib_array = arr[0].split('.')
            if len(bib_array) == 2:
                if bib_array[0].strip().isdigit() and bib_array[1].strip().isdigit():
                    self.variant = arr[1].strip()
                    self.number = bib_array[0].strip()
                    self.leg = bib_array[1].strip()
                    return 1
        return 0

    def get_variant_text(self):
        return "{}.{}: {}".format(self.number, self.leg, self.variant)

    def is_finished(self):
        res = self.get_result()
        if res:
            return True
        return False

    def is_correct(self):
        res = self.get_result()
        if res:
            assert isinstance(res, Result)
            return res.status == ResultStatus.OK
        return True

    def set_bib(self):
        if self.person:
            assert isinstance(self.person, Person)
            self.person.bib = self.get_bib()

    def set_person(self, person):
        self.person = person

    def get_person(self):
        return self.person

    def set_result(self, result):
        self.result = result

    def get_result(self):
        return self.result

    def set_start_time(self, time):
        person = self.get_person()
        if person and isinstance(person, Person):
            person.start_time = time

    def get_finish_time(self):
        res = self.get_result()
        if res:
            assert isinstance(res, Result)
            return res.get_finish_time()
        return None

    def get_start_time(self):
        res = self.get_result()
        if res:
            assert isinstance(res, Result)
            return res.get_start_time()
        return None

    def set_start_time_from_previous(self):
        if self.leg > 1:
            prev_leg = self.get_prev_leg()
            if prev_leg:
                assert isinstance(prev_leg, RelayLeg)
                if prev_leg.is_finished():
                    self.set_start_time(prev_leg.get_finish_time())
                    return 1
        return 0

    def set_place(self, place):
        res = self.get_result()
        if res and isinstance(res, Result):
            res.place = place


class RelayTeam(object):
    def __init__(self, r):
        self.race = r
        self.group = None  # type:Group
        self.legs = []  # type:list[RelayLeg]
        self.description = ''  # Name of team, optional
        self.bib_number = None  # bib
        self.last_finished_leg = 0
        self.last_correct_leg = 0
        self.place = 0

    def __eq__(self, other):
        if self.get_is_status_ok() == self.get_is_status_ok():
            if self.get_lap_finished() == other.get_lap_finished():
                if self.get_time() == other.get_time():
                    return True
        return False

    def __gt__(self, other):
        if self.get_is_status_ok() and not other.get_is_status_ok():
            return False

        if not self.get_is_status_ok() and other.get_is_status_ok():
            return True

        if self.get_lap_finished() != other.get_lap_finished():
            return self.get_lap_finished() < other.get_lap_finished()

        return self.get_time() > other.get_time()

    def get_all_results(self):
        """return: all results of persons, connected with team"""
        pass

    def add_result(self, result):
        """Add new result to the team"""
        leg = RelayLeg(self)
        leg.set_result(result)
        leg.set_person(result.person)
        self.legs.append(leg)

    def set_leg_for_person(self, person, leg):
        """Set leg for person"""
        pass

    def set_bibs(self, number):
        """Set bibs for all members, e.g. 1001, 2001, 3001 for 1,2,3 legs of team #1"""

    def set_start_times(self):
        """Set start time as finish of previous leg for all members"""
        for i in self.legs:
            assert isinstance(i, RelayLeg)
            i.set_start_time_from_previous()

    def get_time(self):
        if len(self.legs):
            last_finish = self.legs[-1].get_finish_time()
            start = self.legs[0].get_start_time()
            return last_finish - start
        return None

    def get_lap_finished(self):
        """quantity of already finished laps"""
        finished_qty = 0
        for leg in self.legs:
            assert isinstance(leg, RelayLeg)
            if leg.is_finished():
                finished_qty += 1
            else:
                return finished_qty
        return finished_qty

    def get_correct_lap_count(self):
        """quantity of successfully finished laps"""

    def get_is_status_ok(self):
        """get the whole status of team - OK if all laps are OK"""
        for leg in self.legs:
            assert isinstance(leg, RelayLeg)
            if not leg.is_correct():
                return False
        return True

    def set_place(self, place):
        self.place = place
        for i in self.legs:
            i.set_place(place)


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
