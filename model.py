from peewee import *

database_proxy = Proxy()


class BaseModel(Model):
    class Meta:
        database = database_proxy


class Settings(BaseModel):
    name = CharField()
    value = TextField()


class Qualification(BaseModel):
    pass


class Fee(BaseModel):
    pass


class Entry(BaseModel):
    pass


class RelayTeam(BaseModel):
    pass


class RaceStatus(BaseModel):
    """
    value: Applied
    value: Proposed
    value: Sanctioned
    value: Canceled
    value: Rescheduled
    """
    value = CharField()


class Race(BaseModel):
    name = TextField()
    start_time = DateTimeField()  # full date, including the day e.g. 2017-03-07 11:00:00
    end_time = DateTimeField()
    status = ForeignKeyField(RaceStatus)
    url = TextField(null=True)
    information = TextField(null=True)


class Course(BaseModel):
    name = TextField()
    course_family = TextField(null=True)
    length = DoubleField(null=True)
    climb = DoubleField(null=True)
    number_of_controls = DoubleField(null=True)
    race = ForeignKeyField(Race)  # connection to the race
    controls_text = TextField()  # JSON with legs and controls. If you have 500 courses for relay, it will be faster


class CourseControl(BaseModel):
    course = ForeignKeyField(Course)
    control = TextField()
    map_text = TextField(null=True)
    leg_length = DoubleField(null=True)
    score = DoubleField()
    is_radio = BooleanField()  # specify if the control is used as radio/TV control
    status = TextField()  # enabled / disabled - e.g. was stolen, broken


class ResultStatus(BaseModel):
    """
    value: OK
    value: Finished
    value: MissingPunch
    value: Disqualified
    value: DidNotFinish
    value: Active
    value: Inactive
    value: OverTime
    value: SportingWithdrawal
    value: NotCompeting
    value: Moved
    value: MovedUp
    value: DidNotStart
    value: DidNotEnter
    value: Cancelled
    """
    value = CharField()


class Country(BaseModel):
    name = CharField()
    code2 = CharField(max_length=2)
    code3 = CharField(max_length=3)
    digital_code = CharField()
    code = CharField()


class Contact(BaseModel):
    name = CharField()
    value = TextField()


class Address(BaseModel):
    care_of = TextField()
    street = TextField()
    zip_code = TextField()
    city = TextField()
    state = TextField()
    country = ForeignKeyField(Country)


class Team(BaseModel):
    name = TextField()
    address = ForeignKeyField(Address, null=True)


class Person(BaseModel):
    name = TextField()
    surname = TextField(null=True)
    sex = CharField(null=True, max_length=1)
    year = SmallIntegerField(null=True)  # sometime we have only year of birth
    birth_date = DateField(null=True)
    team = ForeignKeyField(Team, null=True)
    nationality = ForeignKeyField(Country, null=True)
    address = ForeignKeyField(Address, null=True)
    contact = ForeignKeyField(Contact, null=True)
    world_code = TextField(null=True)  # WRE ID for orienteering and the same
    national_code = TextField(null=True)
    rank = DecimalField(null=True)  # position/scores in word ranking
    qual = ForeignKeyField(Qualification)  # qualification, used in Russia only


class ControlCard(BaseModel):
    person = ForeignKeyField(Person, null=True)
    name = CharField()
    value = TextField()
    is_rented = BooleanField(null=True)  # either card is own or should be returned
    is_returned = BooleanField(null=True)  # used to control the returning of rented cards


class Group(BaseModel):
    """
    Should have name 'Class' according to IOF spec, but this word is reserved in Python
    """
    name = TextField()  # short name, max 5-6 chars e.g. M17
    long_name = TextField()  # to print in official results e.g. 'Juniors before 17 years"
    course = ForeignKeyField(Course)

    sex = TextField(null=True)  # limitation for entry
    min_age = IntegerField(null=True)
    max_age = IntegerField(null=True)

    fee = ForeignKeyField(Fee, null=True)
    max_time = IntegerField(null=True)  # max time for disqualification
    qual_assign_text = TextField(null=True)  # JSON with rules for Qualification calculation (1:MS, 2-6:KMS etc.)
    start_interval = IntegerField(null=True)
    start_corridor = IntegerField(null=True)  # number of start corridor
    order_in_corridor = IntegerField(null=True)  # order in start corridor for automatic start time/bib calculation


class Start(BaseModel):
    group = ForeignKeyField(Group)  # changed from course by SK
    person = ForeignKeyField(Person)
    # TODO: control_card = ForeignKeyField(Person)
    course = ForeignKeyField(Course)
    bib_number = CharField()
    start_time = DateTimeField(null=True)
    comment = TextField(null=True)  # comment (taken from the entry or entered manually)
    competing_status = TextField(null=True)  # can de a dictionary?
    # usual
    # not_ranked - out of team, not to give scores (e.g. team consist of 6 persons, 7th and 8th are not ranked)
    # not_qualified - won't be in official results
    entry = ForeignKeyField(Entry, null=True)  # connection with the Entry object
    relay_team = ForeignKeyField(RelayTeam, null=True)  # conection with relay team.
    relay_leg = IntegerField(null=True)  # relay leg. Possible to calculate it from the bib number
    start_group = IntegerField(null=True)  # used in drawing, to specify red/ping and other start groups
    penalty_time = DecimalField(null=True)  # time of penalties (marked route, false start)
    penalty_laps = IntegerField(null=True)  # count of penalty legs (marked route)


class Result(BaseModel):
    start = ForeignKeyField(Start)
    finish_time = DateTimeField(null=True)
    status = ForeignKeyField(ResultStatus)
    split_time = TextField(null=True)
    control_card = ForeignKeyField(ControlCard)
