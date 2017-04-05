from peewee import *

database_proxy = Proxy()


class BaseModel(Model):
    class Meta:
        database = database_proxy


class Settings(BaseModel):
    name = CharField()
    value = TextField()


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
    is_radio = TextField()  # specify if the control is used as radio/TV control
    status = TextField()  # enabled / disabled - e.g. was stolen, broken


class RaceStatus(BaseModel):
    """
    value: Applied
    value: Proposed
    value: Sanctioned
    value: Canceled
    value: Rescheduled
    """
    value = CharField()


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


class Race(BaseModel):
    name = TextField()
    start_time = DateTimeField()  # full date, including the day e.g. 2017-03-07 11:00:00
    end_time = DateTimeField()
    status = ForeignKeyField(RaceStatus)
    url = TextField(null=True)
    information = TextField(null=True)


class Team(BaseModel):
    name = TextField()
    address = ForeignKeyField(Address, null=True)


class Person(BaseModel):
    name = TextField()
    surname = TextField(null=True)
    year = SmallIntegerField()  # sometime we have only year of birth
    birth_date = DateField(null=True)
    team = ForeignKeyField(Team, null=True)
    nationality = ForeignKeyField(Country, null=True)
    address = ForeignKeyField(Address, null=True)
    contact = ForeignKeyField(Contact, null=True)
    world_code = TextField()  # WRE ID for orienteering and the same
    national_code = TextField()
    rank = DecimalField()  # position/scores in word ranking
    qual = ForeignKeyField(Qualification)  # qualification, used in Russia only


class ControlCard(BaseModel):
    person = ForeignKeyField(Person)
    name = CharField()
    value = TextField()
    is_rented = BooleanField()  # either card is own or should be returned
    is_returned = BooleanField()  # used to control the returning of rented cards


class Start(BaseModel):
    group = ForeignKeyField(Group)  # changed from course by SK
    person = ForeignKeyField(Person)
    # TODO: control_card = ForeignKeyField(Person)
    course = ForeignKeyField(Course)
    bib_number = CharField()
    start_time = DateTimeField()
    comment = TextField()  # comment (taken from the entry or entered manually)
    competing_status = TextField()  # can de a dictionary?
    # usual
    # not_ranked - out of team, not to give scores (e.g. team consist of 6 persons, 7th and 8th are not ranked)
    # not_qualified - won't be in official results
    entry = ForeignKeyField(Entry)  # connection with the Entry object
    relay_team = ForeignKeyField(RelayTeam)  # conection with relay team.
    relay_leg = IntegerField()  # relay leg. Possible to calculate it from the bib number
    start_group = IntegerField()  # used in drawing, to specify red/ping and other start groups


class Result(BaseModel):
    start = ForeignKeyField(Start)
    finish_time = DateTimeField()
    status = ForeignKeyField(ResultStatus)
    split_time = TextField(null=True)
    control_card = ForeignKeyField(ControlCard)
    result = TextField()  # it's better to store calculated result to do fast return in case of mass requests
    place = IntegerField()  # it's better to store calculated place and update it after each readout / disqualification
    penalty_time = DecimalField()  # time of penalties (marked route, false start)
    penalty_laps = IntegerField()  # count of penalty legs (marked route)


class Group(BaseModel):
    """
    Should have name 'Class' according to IOF spec, but this word is reserved in Python
    """
    name = TextField()  # short name, max 5-6 chars e.g. M17
    long_name = TextField()  # to print in official results e.g. 'Juniors before 17 years"
    course = ForeignKeyField(Course)

    sex = TextField()  # limitation for entry
    min_age = IntegerField()
    max_age = IntegerField()

    fee = ForeignKeyField(Fee)
    max_time = IntegerField()  # max time for disqualification
    qual_assign_text = TextField()  # JSON with rules for Qualification calculation (1:MS, 2-6:KMS etc.) - Russia only
    start_interval = IntegerField()
    start_corridor = IntegerField()  # number of start corridor
    order_in_corridor = IntegerField()  # order in start corridor for automatic start time/bib calculation in all groups


class Fee(BaseModel):
    pass


class Entry(BaseModel):
    pass


class RelayTeam(BaseModel):
    pass


class Qualification(BaseModel):
    pass
