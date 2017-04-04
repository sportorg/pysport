from playhouse.migrate import *
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


class CourseControl(BaseModel):
    course = ForeignKeyField(Course)
    control = TextField()
    map_text = TextField(null=True)
    leg_length = DoubleField(null=True)
    score = DoubleField()


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
    start_time = DateTimeField()
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
    birth_date = DateField(null=True)
    team = ForeignKeyField(Team, null=True)
    nationality = ForeignKeyField(Country, null=True)
    address = ForeignKeyField(Address, null=True)
    contact = ForeignKeyField(Contact, null=True)


class ControlCard(BaseModel):
    person = ForeignKeyField(Person)
    name = CharField()
    value = TextField()


class Start(BaseModel):
    race = ForeignKeyField(Race)
    person = ForeignKeyField(Person)
    course = ForeignKeyField(Course)
    bib_number = CharField()
    start_time = DateTimeField()


class Result(BaseModel):
    start = ForeignKeyField(Start)
    finish_time = DateTimeField()
    status = ForeignKeyField(ResultStatus)
    split_time = TextField(null=True)
    control_card = ForeignKeyField(ControlCard)
