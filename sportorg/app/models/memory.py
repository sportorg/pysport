class Model(object):
    @classmethod
    def create(cls, **kwargs):
        o = cls()
        for key, value in kwargs.items():
            if hasattr(o, key):
                setattr(o, key, value)

        return o

    @classmethod
    def update(cls, **kwargs):
        for key, value in kwargs.items():
            if hasattr(cls, key):
                setattr(cls, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, val):
        if hasattr(self, key):
            setattr(self, key, val)


class Country(Model):
    name = ''
    code2 = ''
    code3 = ''
    digital_code = ''
    code = ''


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


class Settings(object):
    competition_type = CompetitionType.PREDETERMINED
    append_exist_person = False
    print_person_result = False
    check_punches = True


class Address(Model):
    care_of = ''
    street = ''
    zip_code = ''
    city = ''
    state = ''
    country = Country()


class Contact(Model):
    name = ''
    value = ''


class Organization(Model):
    name = ''
    address = Address()
    contact = Contact()
    country = Country()
    city = ''
    region = ''


class OrganizationList(list):
    pass


class CourseControl(Model):
    code = ''
    length = 0
    order = None


class CourseControlList(list):
    pass


class Course(Model):
    name = ''
    type = ''
    bib = ''
    length = 0
    climb = 0
    controls = None

    def get_code_list(self):
        ret = list()
        for i in self.controls:
            assert isinstance(i, CourseControl)
            ret.append(str(i.code))
        return ret


class CourseList(list):
    pass


class Group(Model):
    name = ''
    course = Course()
    price = 0
    long_name = ''
    sex = ''

    min_age = 0
    max_age = 0

    max_time = None  # datetime
    qual_assign_text = ''
    start_interval = 0
    start_corridor = 0
    order_in_corridor = 0


class GroupList(list):
    pass


class Result(Model):
    card_number = None
    start_time = None
    finish_time = None
    punches = list()
    penalty_time = 0  # time of penalties (marked route, false start)
    penalty_laps = 0  # count of penalty legs (marked route)
    status = None
    result = 0
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


class ResultList(list):
    pass


class Person(Model):
    name = ''
    surname = ''
    sex = ''

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
    world_code = ''  # WRE ID for orienteering and the same
    national_code = ''
    rank = ''  # position/scores in word ranking
    qual = ''  # qualification, used in Russia only


class PersonList(list):
    pass


class RaceData(Model):
    name = ''
    organisation = None
    start_time = None
    end_time = None
    live_url = None


class Race(Model):
    data = RaceData()
    courses = CourseList()
    groups = GroupList()
    persons = PersonList()
    results = ResultList()
    organizations = OrganizationList()
    settings = Settings()


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
        day = day - 1

    if day in event:
        return event[day]
    else:
        return Race()
