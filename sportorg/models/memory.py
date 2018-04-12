import uuid
from abc import abstractmethod
from datetime import date
from enum import IntEnum, Enum
from typing import Dict, List, Any

import datetime
import dateutil.parser

from sportorg.core.model import Model
from sportorg.core.otime import OTime
from sportorg.language import _
from sportorg.utils.time import str_to_date, date_to_str


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


class PrintableValue(object):
    def __init__(self, value, printable_name):
        self.value = value
        self.printable_name = printable_name


class _TitleType(Enum):
    def __new__(cls, value):
        obj = object.__new__(cls)
        obj._value_ = value.value
        obj._title  = value.printable_name
        return obj

    def __str__(self):
        return "%s" % self._name_

    def __repr__(self):
        return self.__str__()

    def get_title(self):
        return self._title

    @classmethod
    def get_titles(cls):
        ret = [obj.get_title() for obj in cls]
        return ret


class Sex(_TitleType):
    MF = PrintableValue(0, _('MF'))
    M = PrintableValue(1, _('M'))
    F = PrintableValue(2, _('F'))


class RaceType(_TitleType):
    INDIVIDUAL_RACE = PrintableValue(0, _('Individual race'))
    MASS_START = PrintableValue(1, _('Mass start'))
    PURSUIT = PrintableValue(2, _('Pursuit'))
    RELAY = PrintableValue(3, _('Relay'))
    ONE_MAN_RELAY = PrintableValue(4, _('One man relay'))
    SPRINT_RELAY = PrintableValue(5, _('Sprint relay'))


class ResultStatus(_TitleType):
    NONE = PrintableValue(0, _('None'))
    OK = PrintableValue(1, _('OK'))
    FINISHED = PrintableValue(2, _('Finished'))
    MISSING_PUNCH = PrintableValue(3,  _('Missing punch'))
    DISQUALIFIED = PrintableValue(4, _('DSQ'))
    DID_NOT_FINISH = PrintableValue(5, _('DNF'))
    ACTIVE = PrintableValue(6, _('Active'))
    INACTIVE = PrintableValue(7, _('Inactive'))
    OVERTIME = PrintableValue(8, _('Overtime'))
    SPORTING_WITHDRAWAL = PrintableValue(9, _('Sporting withdrawal'))
    NOT_COMPETING = PrintableValue(10, _('Not competing'))
    MOVED = PrintableValue(11, _('Moved'))
    MOVED_UP = PrintableValue(12, _('Moved up'))
    DID_NOT_START = PrintableValue(13, _('DNS'))
    DID_NOT_ENTER = PrintableValue(14, _('Did not enter'))
    CANCELLED = PrintableValue(15, _('Cancelled'))


class Country(Model):
    def __init__(self):
        self.name = ''
        self.code2 = ''
        self.code3 = ''
        self.digital_code = ''
        self.code = ''

    def __repr__(self):
        return self.name

    def to_dict(self):
        return {
            'object': self.__class__.__name__,
            'name': self.name,
            'code2': self.code2,
            'code3': self.code3,
            'digital_code': self.digital_code,
            'code': self.code,
        }

    def update_data(self, data):
        self.name = str(data['name'])
        self.code2 = str(data['code2'])
        self.code3 = str(data['code3'])
        self.digital_code = str(data['digital_code'])
        self.code = str(data['code'])


class Address(Model):
    def __init__(self):
        self.care_of = ''
        self.street = ''
        self.zip_code = ''
        self.city = ''
        self.state = ''
        self.country = Country()

    def to_dict(self):
        return {
            'object': self.__class__.__name__,
            'care_of': self.care_of,
            'street': self.street,
            'zip_code': self.zip_code,
            'city': self.city,
            'state': self.state,
            'country': self.country.to_dict()
        }

    def update_data(self, data):
        self.care_of = str(data['care_of'])
        self.street = str(data['street'])
        self.zip_code = str(data['zip_code'])
        self.city = str(data['city'])
        self.state = str(data['state'])
        self.country.update_data(data['country'])


class Contact(Model):
    def __init__(self):
        self.name = ''
        self.value = ''

    def __repr__(self):
        return '{} {}'.format(self.name, self.value)

    def to_dict(self):
        return {
            'object': self.__class__.__name__,
            'name': self.name,
            'value': self.value,
        }

    def update_data(self, data):
        self.name = str(data['name'])
        self.value = str(data['value'])


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
            'object': self.__class__.__name__,
            'id': str(self.id),
            'name': self.name,
            'address': self.address.to_dict(),
            'contact': self.contact.to_dict(),
            'count_person': self.count_person,
        }

    def update_data(self, data):
        self.name = str(data['name'])
        self.contact.update_data(data['contact'])
        self.address.update_data(data['address'])


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
            'object': self.__class__.__name__,
            'code': self.code,
            'length': self.length
        }

    def update_data(self, data):
        self.code = str(data['code'])
        self.length = int(data['length'])


class CoursePart(Model):
    def __init__(self):
        self.controls = []  # type: List[CourseControl]
        self.control_count = 0
        self.is_free = False

    def to_dict(self):
        controls = [control.to_dict() for control in self.controls]
        return {
            'object': self.__class__.__name__,
            'controls': controls,
            'control_count': self.control_count,
            'is_free': self.is_free,
        }


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
            if '*' in control.code or '%' in control.code or '(' in control.code:
                return True

        return False

    def get_code_list(self):
        ret = []
        for i in self.controls:
            assert isinstance(i, CourseControl)
            ret.append(str(i.code))
        return ret

    def to_dict(self):
        controls = [control.to_dict() for control in self.controls]
        return {
            'object': self.__class__.__name__,
            'id': str(self.id),
            'controls': controls,
            'bib': self.bib,
            'name': self.name,
            'length': self.length,
            'climb': self.climb,
            'corridor': self.corridor
        }

    def update_data(self, data):
        self.name = str(data['name'])
        self.bib = int(data['bib'])
        self.length = int(data['length'])
        self.climb = int(data['climb'])
        self.corridor = int(data['corridor'])
        self.controls = []
        for item in data['controls']:
            control = CourseControl()
            control.update_data(item)
            self.controls.append(control)


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
            'object': self.__class__.__name__,
            'id': str(self.id),
            'name': self.name,
            'course_id': str(self.course.id) if self.course else None,
            'long_name': self.long_name,
            'price': self.price,
            'sex': self.sex.value,
            'min_age': self.min_age,
            'max_age': self.max_age,
            'max_time': self.max_time.to_msec(),
            'start_interval': self.start_interval.to_msec(),
            'start_corridor': self.start_corridor,
            'order_in_corridor': self.order_in_corridor,
            'first_number': self.first_number,
            'ranking': self.ranking.to_dict() if self.ranking else None,
            '__type': self.__type.value if self.__type else None,
            'relay_legs': self.relay_legs,

        }

    def update_data(self, data):
        self.name = str(data['name'])
        self.long_name = str(data['long_name'])
        self.price = int(data['price'])
        self.sex = Sex(int(data['sex']))
        self.min_age = int(data['min_age'])
        self.max_age = int(data['max_age'])
        self.max_time = OTime(msec=int(data['max_time']))
        self.start_interval = OTime(msec=int(data['start_interval']))
        self.start_corridor = int(data['start_corridor'])
        self.order_in_corridor = int(data['order_in_corridor'])
        self.first_number = int(data['first_number'])
        self.relay_legs = int(data['relay_legs'])
        if 'ranking' in data:
            if data['ranking']:
                self.ranking = Ranking()
                self.ranking.update_data(data['ranking'])
        if data['__type']:
            self.__type = RaceType(int(data['__type']))


class Split(Model):
    def __init__(self):
        self.code = 0
        self.days = 0
        self.time = None  # type: OTime
        self.pace = None  # type: OTime

    def __eq__(self, other):
        assert isinstance(other, Split)
        if self.code == 0 or other.code == 0:
            return False
        if self.time is None or other.time is None:
            return False
        return self.code == other.code and self.time == other.time

    def to_dict(self):
        return {
            'object': self.__class__.__name__,
            'days': self.days,
            'code': self.code,
            'time': self.time.to_msec() if self.time else None,
        }

    def update_data(self, data):
        self.code = int(data['code'])
        if data['time']:
            self.time = OTime(msec=data['time'])
        if 'days' in data:
            self.days = int(data['days'])


class Result:
    def __init__(self):
        if type(self) == Result:
            raise Exception("<Result> is abstracted")
        self.id = uuid.uuid4()
        self.days = 0
        self.start_time = None  # type: OTime
        self.finish_time = OTime.now()  # type: OTime
        self.person = None  # type: Person
        self.status = ResultStatus.OK
        self.status_comment = ''
        self.penalty_time = None  # type: OTime
        self.penalty_laps = 0  # count of penalty legs (marked route)
        self.place = 0
        self.scores = 0
        self.assigned_rank = Qualification.NOT_QUALIFIED
        self.diff = None  # type: OTime

    def __str__(self):
        return str(self.system_type)

    def __repr__(self):
        return 'Result {} {}'.format(self.system_type, self.status)

    def __eq__(self, other):
        eq = self.system_type and other.system_type
        if self.start_time and other.start_time:
            eq = eq and self.start_time == other.start_time
        if self.finish_time and other.finish_time:
            eq = eq and self.finish_time == other.finish_time
        else:
            return False
        return eq

    def __gt__(self, other):
        if self.status != other.status:
            return self.status.value > other.status.value
        return self.get_result_otime() > other.get_result_otime()

    @property
    @abstractmethod
    def system_type(self) -> SystemType:
        pass

    def to_dict(self):
        return {
            'object': self.__class__.__name__,
            'id': str(self.id),
            'system_type': self.system_type.value,
            'person_id': str(self.person.id) if self.person else None,
            'days': self.days,
            'start_time': self.start_time.to_msec() if self.start_time else None,
            'finish_time': self.finish_time.to_msec() if self.finish_time else None,
            'diff': self.diff.to_msec() if self.diff else None,
            'penalty_time': self.penalty_time.to_msec() if self.penalty_time else None,
            'status': self.status.value,
            'status_comment': self.status_comment,
            'penalty_laps': self.penalty_laps,
            'place': self.place,
            'scores': self.scores,
            'assigned_rank': self.assigned_rank.value,
        }

    def update_data(self, data):
        self.status = ResultStatus(int(data['status']))
        self.penalty_laps = int(data['penalty_laps'])
        self.scores = data['scores']
        if str(data['place']).isdigit():
            self.place = int(data['place'])
        self.assigned_rank = Qualification.get_qual_by_code(data['assigned_rank'])
        if data['start_time']:
            self.start_time = OTime(msec=data['start_time'])
        if data['finish_time']:
            self.finish_time = OTime(msec=data['finish_time'])
        if data['penalty_time']:
            self.penalty_time = OTime(msec=data['penalty_time'])
        if 'status_comment' in data:
            self.status_comment = data['status_comment']
        if 'days' in data:
            self.days = int(data['days'])

    def clear(self):
        pass

    def get_result(self):
        if not self.is_status_ok():
            if self.status_comment:
                return self.status_comment
            return self.status.get_title()

        if not self.person:
            return ''

        return str(self.get_finish_time() - self.get_start_time() + self.get_penalty_time())

    def get_result_for_sort(self):
        ret = self.get_result_otime()
        return self.status, ret.to_msec()

    def get_result_otime(self):
        return self.get_finish_time() - self.get_start_time() + self.get_penalty_time()

    def get_start_time(self):
        if self.start_time and self.start_time.to_msec():
            return self.start_time
        if self.person and self.person.start_time and self.person.start_time.to_msec():
            return self.person.start_time
        return OTime()

    def get_finish_time(self):
        if self.finish_time:
            return self.finish_time

        return OTime.now()

    def get_penalty_time(self):
        if self.penalty_time:
            return self.penalty_time
        return OTime()

    def get_place(self):
        """Returns text for place column in results"""
        if self.place > 0:
            return self.place
        if self.person and self.person.is_out_of_competition:
            return _('o/c')
        return ''

    def get_course_splits(self, course=None):
        return []

    def check(self, course=None):
        return True

    def is_status_ok(self):
        return self.status == ResultStatus.OK

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
        self.sportident_card = 0
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
                eq = eq and self.splits[i].time == other.splits[i].time
        else:
            return False
        return eq

    def to_dict(self):
        data = super().to_dict()
        data['splits'] = [split.to_dict() for split in self.splits]
        data['sportident_card'] = self.sportident_card

        return data

    def update_data(self, data):
        super().update_data(data)
        self.sportident_card = int(data['sportident_card'])
        self.splits = []
        for item in data['splits']:
            split = Split()
            split.update_data(item)
            self.splits.append(split)

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

        return OTime()

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

        # return 0 to avoid incorrect results
        return OTime()

    def clear(self):
        self.__start_time = None
        self.__finish_time = None

    def get_course_splits(self, course=None):
        result_splits = []
        for i, split in enumerate(self.splits):
            if not i or split.code != self.splits[i - 1].code:
                result_splits.append(split)
        if not course or course.is_unknown():
            return result_splits
        max_len = len(result_splits)
        splits = []
        i = 0
        for control in course.controls:
            if i >= max_len:
                break

            while not str(result_splits[i].code) in control.code:
                # skip incorrect punches
                i += 1
                if i >= max_len:
                    break

            if i >= max_len:
                break

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

        self.sportident_card = 0
        self.bib = 0

        self.birth_date = None  # type: date
        self.organization = None  # type: Organization
        self.group = None  # type: Group
        self.nationality = None  # type: Country
        self.address = None  # type: Address
        self.contact = []  # type: List[Contact]
        self.world_code = None  # WRE ID for orienteering and the same
        self.national_code = None
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

    def get_year(self):
        """Get year from birth_date. If only year is used in the event, it's stored as 01-01-year"""
        if self.birth_date:
            return self.birth_date.year
        return 0

    def set_year(self, year):
        """Change only year of birth_date"""
        if year == 0:
            self.birth_date = None
            return

        if self.birth_date:
            self.birth_date = date(year, self.birth_date.month, self.birth_date.day)
        else:
            self.birth_date = date(year, 1, 1)

    @property
    def full_name(self):
        surname = self.surname
        if surname:
            surname += ' '
        return '{}{}'.format(surname, self.name)

    def to_dict(self):
        return {
            'object': self.__class__.__name__,
            'id': str(self.id),
            'name': self.name,
            'surname': self.surname,
            'sex': self.sex.value,
            'sportident_card': self.sportident_card,
            'bib': self.bib,
            'birth_date': str(self.birth_date) if self.birth_date else None,
            'group_id': str(self.group.id) if self.group else None,
            'organization_id': str(self.organization.id) if self.organization else None,
            'nationality': self.nationality.to_dict() if self.nationality else None,
            'address': self.address.to_dict() if self.address else None,
            'contact': [],
            'world_code': self.world_code,
            'national_code': self.national_code,
            'qual': self.qual.value,
            'is_out_of_competition': self.is_out_of_competition,
            'is_paid': self.is_paid,
            'is_rented_sportident_card': self.is_rented_sportident_card,
            'is_personal': self.is_personal,
            'comment': self.comment,
            'start_time': self.start_time.to_msec() if self.start_time else None,
            'start_group': self.start_group,
        }

    def update_data(self, data):
        self.name = str(data['name'])
        self.surname = str(data['surname'])
        self.sex = Sex(int(data['sex']))
        self.sportident_card = int(data['sportident_card'])
        self.bib = int(data['bib'])
        self.contact = []
        self.world_code = data['world_code']
        self.national_code = data['national_code']
        self.qual = Qualification.get_qual_by_code(data['qual'])
        self.is_out_of_competition = bool(data['is_out_of_competition'])
        self.is_paid = bool(data['is_paid'])
        self.is_rented_sportident_card = bool(data['is_rented_sportident_card'])
        self.is_personal = bool(data['is_personal'])
        self.comment = str(data['comment'])
        self.start_group = int(data['start_group'])
        if data['start_time'] is not None:
            self.start_time = OTime(msec=int(data['start_time']))
        if data['birth_date']:
            self.birth_date = dateutil.parser.parse(data['birth_date']).date()
        elif 'year' in data and data['year']:  # back compatibility with v 1.0.0
            self.set_year(int(data['year']))

    def to_dict_data(self, course=None):
        sportident_card = ''
        if self.sportident_card:
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
            'team_subject': self.organization.address.state if self.organization is not None else '',
            'group': self.group.name if self.group is not None else '',
            'group_start_corridor': self.group.start_corridor if self.group is not None else 0,
            'price': self.group.price if self.group is not None else 0,
            'qual': self.qual.get_title(),
            'year': self.get_year() if self.get_year() else '',
            'sportident_card': sportident_card,
            'start': str(self.start_time),
            'comment': self.comment,
            'is_out_of_competition': self.is_out_of_competition,
            'is_rented': self.is_rented_sportident_card,
            'is_paid': self.is_paid,
        }


class RaceData(Model):
    def __init__(self):
        self.title = ''
        self.description = ''
        self.location = ''
        self.chief_referee = ''
        self.secretary = ''
        self.url = ''
        self.race_type = RaceType.INDIVIDUAL_RACE
        self.start_datetime = None  # type: datetime
        self.end_datetime = None  # type: datetime
        self.relay_leg_count = 3

    def __repr__(self):
        return 'Race {}'.format(self.title)

    def get_start_datetime(self):
        if self.start_datetime is None:
            return datetime.datetime.now().replace(second=0, microsecond=0)
        return self.start_datetime

    def get_end_datetime(self):
        if self.end_datetime is None:
            return datetime.datetime.now().replace(second=0, microsecond=0)
        return self.end_datetime

    def get_days(self, date=None):
        if self.start_datetime is None:
            return 0
        if date is None:
            date = datetime.datetime.now()
        return max((date - self.start_datetime).days, 0)

    def to_dict(self):
        return {
            'title': self.title,
            'description': self.description,
            'location': self.location,
            'chief_referee': self.chief_referee,
            'secretary': self.secretary,
            'url': self.url,
            'race_type': self.race_type.value,
            'start_datetime': str(self.start_datetime) if self.start_datetime else None,
            'end_datetime': str(self.end_datetime) if self.end_datetime else None,
            'relay_leg_count': self.relay_leg_count,
        }

    def update_data(self, data):
        self.title = str(data['title'])
        self.description = str(data['description'])
        self.location = str(data['location'])
        self.chief_referee = str(data['chief_referee'])
        self.secretary = str(data['secretary'])
        self.url = str(data['url'])
        self.race_type = RaceType(int(data['race_type']))
        self.relay_leg_count = int(data['relay_leg_count'])
        if data['start_datetime']:
            self.start_datetime = dateutil.parser.parse(data['start_datetime'])
        if data['end_datetime']:
            self.end_datetime = dateutil.parser.parse(data['end_datetime'])


class Race(Model):
    support_obj = {
        'Person': Person,
        'Result': Result,
        'ResultManual': ResultManual,
        'ResultSportident': ResultSportident,
        'Group': Group,
        'Course': Course,
        'Organization': Organization,
    }

    def __init__(self):
        self.id = uuid.uuid4()
        self.data = RaceData()
        self.organizations = []  # type: List[Organization]
        self.courses = []  # type: List[Course]
        self.groups = []  # type: List[Group]
        self.results = []  # type: List[Result]
        self.persons = []  # type: List[Person]
        self.relay_teams = []  # type: List[RelayTeam]
        self.settings = {}  # type: Dict[str, Any]

    def __repr__(self):
        return repr(self.data)

    @property
    def list_obj(self):
        return {
            'Person': self.persons,
            'Result': self.results,
            'ResultManual': self.results,
            'ResultSportident': self.results,
            'Group': self.groups,
            'Course': self.courses,
            'Organization': self.organizations,
        }

    def to_dict_data(self):
        return {
            'title': self.data.title,
            'sub_title': self.data.description,
            'url': self.data.url,
            'location': self.data.location,
            'date': self.data.get_start_datetime().strftime("%d.%m.%Y"),
            'chief_referee': race().data.chief_referee,
            'secretary': race().data.secretary
        }

    def to_dict(self):
        return {
            'object': self.__class__.__name__,
            'id': str(self.id),
            'data': self.data.to_dict(),
            'settings': self.settings,
            'organizations': [item.to_dict() for item in self.organizations],
            'courses': [item.to_dict() for item in self.courses],
            'groups': [item.to_dict() for item in self.groups],
            'results': [item.to_dict() for item in self.results],
            'persons': [item.to_dict() for item in self.persons],
        }

    def update_data(self, dict_obj):
        if 'object' not in dict_obj:
            return
        if dict_obj['object'] == 'Race' and dict_obj['id'] == str(self.id):
            if 'data' in dict_obj:
                self.data.update_data(dict_obj['data'])
            if 'settings' in dict_obj:
                self.settings = dict_obj['settings']
            key_list = ['organizations', 'courses', 'groups', 'persons', 'results']
            for key in key_list:
                if key in dict_obj:
                    for item_obj in dict_obj[key]:
                        self.update_data(item_obj)
            return
        elif dict_obj['object'] not in self.support_obj:
            return

        obj = self.get_obj(dict_obj['object'], dict_obj['id'])
        if obj is None:
            self.create_obj(dict_obj)
        else:
            self.update_obj(obj, dict_obj)

    def get_obj(self, obj_name, obj_id):
        for item in self.list_obj[obj_name]:
            if str(item.id) == obj_id:
                return item

    def update_obj(self, obj, dict_obj):
        obj.update_data(dict_obj)
        if dict_obj['object'] == 'Person':
            obj.group = self.get_obj('Group', dict_obj['group_id'])
            obj.organization = self.get_obj('Organization', dict_obj['organization_id'])
        elif dict_obj['object'] in ['Result', 'ResultManual', 'ResultSportident']:
            obj.person = self.get_obj('Person', dict_obj['person_id'])
        elif dict_obj['object'] == 'Group':
            obj.course = self.get_obj('Course', dict_obj['course_id'])

    def create_obj(self, dict_obj):
        obj = self.support_obj[dict_obj['object']]()
        obj.id = uuid.UUID(dict_obj['id'])
        self.update_obj(obj, dict_obj)
        self.list_obj[dict_obj['object']].insert(0, obj)

    def get_type(self, group: Group):
        if group.get_type():
            return group.get_type()
        return self.data.race_type

    def set_setting(self, setting, value):
        self.settings[setting] = value

    def get_setting(self, setting, nvl_value=None):
        if setting in self.settings:
            return self.settings[setting]
        else:
            return nvl_value

    def get_days(self, date=None):
        return self.data.get_days(date)

    def person_sportident_card(self, person, number=0):
        assert isinstance(person, Person)
        person.sportident_card = number
        for p in self.persons:
            if p.sportident_card == number and p != person:
                p.sportident_card = 0
                p.is_rented_sportident_card = False
                return p

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

    def new_result(self):
        new_result = ResultManual()
        new_result.days = self.get_days()
        return new_result

    def new_sportident_result(self):
        new_result = ResultSportident()
        new_result.days = self.get_days()
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

    def is_relay(self):
        if self.data.race_type == RaceType.RELAY:
            return True
        return False


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

    @classmethod
    def get_qual_by_code(cls, code):
        return cls(code)

    @classmethod
    def get_qual_by_name(cls, name):
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
            'ЗМС': 9
        }
        return cls(qual_reverse[name])

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
            9: 'МСМК'
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
            9: 100
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
        ret['max_time'] = str(self.max_time)
        ret['percent'] = self.percent
        return ret

    def to_dict(self):
        ret = {}
        ret['qual'] = self.qual.value
        ret['use_scores'] = self.use_scores
        ret['max_place'] = str(self.max_place)
        ret['max_time'] = self.max_time.to_msec() if self.max_time else None
        ret['is_active'] = self.is_active
        ret['percent'] = self.percent
        return ret

    def update_data(self, data):
        self.qual = Qualification.get_qual_by_code(int(data['qual']))
        self.use_scores = bool(data['use_scores'])
        self.max_place = int(data['max_place'])
        if data['max_time']:
            self.max_time = OTime(msec=int(data['max_time']))
        self.is_active = bool(data['is_active'])
        self.percent = int(data['percent'])


class Ranking(object):
    def __init__(self):
        self.is_active = False
        self.rank_scores = 0
        self.rank = {}
        self.rank[Qualification.MS] = RankingItem(qual=Qualification.MS, use_scores=False, max_place=2, is_active=False)
        self.rank[Qualification.KMS] = RankingItem(qual=Qualification.KMS, use_scores=False, max_place=6,
                                                   is_active=False)
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

    def to_dict(self):
        ret = {}
        ret['is_active'] = self.is_active
        ret['rank_scores'] = self.rank_scores
        ret['rank'] = []
        for i in self.rank:
            obj = self.rank[i]
            rank = obj.to_dict()
            ret['rank'].append(rank)
        return ret

    def update_data(self, data):
        self.is_active = bool(data['is_active'])
        if 'rank_scores' in data:
            self.rank_scores = int(data['rank_scores'])
        for i in data['rank']:
            rank = RankingItem()
            rank.update_data(i)
            self.rank[rank.qual] = rank


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
            return res.is_status_ok()
        return True

    def is_out_of_competition(self):
        res = self.get_result()
        if res and res.person:
            return res.person.is_out_of_competition
        return False

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
            if self.get_correct_lap_count() == other.get_correct_lap_count():
                if self.get_time() == other.get_time():
                    return True
        return False

    def __gt__(self, other):
        if self.get_is_status_ok() and not other.get_is_status_ok():
            return False

        if not self.get_is_status_ok() and other.get_is_status_ok():
            return True

        if self.get_correct_lap_count() != other.get_correct_lap_count():
            return self.get_correct_lap_count() < other.get_correct_lap_count()

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
            last_correct_leg = self.get_correct_lap_count()
            if last_correct_leg > 0:
                last_finish = self.legs[last_correct_leg-1].get_finish_time()
                start = self.legs[0].get_start_time()
                return last_finish - start
        return OTime()

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
        correct_qty = 0
        for leg in self.legs:
            assert isinstance(leg, RelayLeg)
            if leg.is_correct():
                correct_qty += 1
            else:
                return correct_qty
        return correct_qty

    def get_is_status_ok(self):
        """get the whole status of team - OK if all laps are OK"""
        for leg in self.legs:
            assert isinstance(leg, RelayLeg)
            if not leg.is_correct():
                return False
        return True

    def get_is_all_legs_finished(self):
        # check leg count
        leg_count = race().data.relay_leg_count
        return len(self.legs) >= leg_count

    def get_is_out_of_competition(self):
        """get the whole status of team - OK if any lap is out of competition"""
        for leg in self.legs:
            assert isinstance(leg, RelayLeg)
            if leg.is_out_of_competition():
                return True
        return False

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


_event = [create(Race)]


def new_event(event):
    if len(event):
        global _event
        _event = event


def races():
    return _event


def race(day=None):
    if day is None:
        # TODO: from settings
        day = 0
    else:
        day -= 1

    if day < len(_event):
        return _event[day]
    else:
        return Race()
