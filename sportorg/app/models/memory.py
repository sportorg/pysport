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


class SettingsDict(dict):
    pass


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

    def get_code_list(self):
        ret = list()
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
    punches = list()
    penalty_time = None  # time of penalties (marked route, false start)
    penalty_laps = None  # count of penalty legs (marked route)
    status = None
    result = None
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


class PersonList(list):
    pass


class RaceData(Model):
    name = None
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
    settings = SettingsDict()


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
