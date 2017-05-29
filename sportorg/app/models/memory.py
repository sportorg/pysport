class Country(object):
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


class CompetitionType:
    PREDETERMINED = 'Predetermined'
    SELECTION = 'Selection'
    MARKING = 'Marking'


class Settings:
    competition_type = CompetitionType.PREDETERMINED
    append_exist_person = False
    print_person_result = False
    check_punches = True


class Address(object):
    care_of = ''
    street = ''
    zip_code = ''
    city = ''
    state = ''
    country = Country()


class Contact(object):
    name = ''
    value = ''


class Organization(object):
    name = ''
    address = Address()
    contact = Contact()
    country = Country()


class OrganizationList(list):
    def find(self, name):
        for org in self:
            assert (isinstance(org, Organization))
            if org.name == name:
                return org
        return None


class CourseControl(object):
    code = ''
    length = 0
    order = None


class CourseControlDict(dict):
    def __len__(self) -> int:
        return len(self.keys()) - 1 if len(self.keys()) - 1 >= 0 else len(self.keys())


class Course(object):
    name = ''
    type = ''
    bib = ''
    length = 0
    climb = 0
    controls = CourseControlDict()


class CourseList(list):
    pass


class Group(object):
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
    def find(self, name):
        for group in self:
            assert (isinstance(group, Group))
            if group.name == name:
                return group
        return None


class Result(object):
    card_number = None
    start_time = None
    finish_time = None
    punches = list()
    penalty_time = 0  # time of penalties (marked route, false start)
    penalty_laps = 0  # count of penalty legs (marked route)
    status = None

    def __eq__(self, other):
        eq = self.card_number == other.card_number
        eq = eq and self.start_time == other.start_time
        eq = eq and self.finish_time == other.finish_time
        eq = eq and self.punches == other.punches
        return eq


class ResultList(list):
    pass


class Person(object):
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


class RaceData(object):
    name = ''
    organisation = None
    start_time = None
    end_time = None
    live_url = None


class Race(object):
    data = RaceData()
    courses = CourseList()
    groups = GroupList()
    persons = PersonList()
    results = ResultList()
    organizations = OrganizationList()
    settings = Settings()


def create(obj, **kwargs):
    o = obj()
    for key, value in kwargs.items():
        if hasattr(o, key):
            setattr(o, key, value)

    return o


def update(obj, **kwargs):
    for key, value in kwargs.items():
        if hasattr(obj, key):
            setattr(obj, key, value)


def find(iterable: list, obj, **kwargs):
    if len(kwargs.items()) == 0:
        return None
    return_all = kwargs.pop('return_all', False)
    results = []
    for item in iterable:
        assert (isinstance(item, obj))
        f = True
        for key, value in kwargs.items():
            assert (hasattr(obj, key))
            if getattr(obj, key) != value:
                f = False
        if f:
            if return_all:
                results.append(item)
            else:
                return item

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
