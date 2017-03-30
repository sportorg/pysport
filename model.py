from playhouse.migrate import *
from peewee import *

database_proxy = Proxy()


class BaseModel(Model):
    class Meta:
        database = database_proxy


class Extensions(BaseModel):
    name = TextField()
    value = TextField()


class ControlCard(BaseModel):
    name = TextField()
    value = TextField()


class CourseControl(BaseModel):
    control = TextField()
    map_text = TextField()
    leg_length = DoubleField()
    score = DoubleField()


class Course(BaseModel):
    name = TextField()
    course_family = TextField()
    length = DoubleField()
    climb = DoubleField()
    course_control = ForeignKeyField(CourseControl)
    map_id = IntegerField()
    number_of_controls = DoubleField()


class EventStatus(BaseModel):
    """
    value: Applied
    value: Proposed
    value: Sanctioned
    value: Canceled
    value: Rescheduled
    """
    value = TextField()


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
    value = TextField()


class Country(BaseModel):
    pass


class Contact(BaseModel):
    pass


class Address(BaseModel):
    care_of = TextField()
    street = TextField()
    zip_code = TextField()
    city = TextField()
    state = TextField()
    country = ForeignKeyField(Country)


class Event(BaseModel):
    name = TextField()
    start_time = DateTimeField()
    end_time = DateTimeField()
    status = ForeignKeyField(EventStatus)
    url = TextField()
    information = TextField()


class Team(BaseModel):
    name = TextField()
    address = ForeignKeyField(Address)


class Person(BaseModel):
    name = TextField()
    surname = TextField()
    birth_date = DateField(null=True)
    team = ForeignKeyField(Team, null=True)
    nationality = ForeignKeyField(Country, null=True)
    address = ForeignKeyField(Address, null=True)
    contact = ForeignKeyField(Contact, null=True)


class Start(BaseModel):
    event = ForeignKeyField(Event)
    person = ForeignKeyField(Person)
    course = ForeignKeyField(Course)
    bib_number = TextField()
    start_time = DateTimeField()


class SplitTime(BaseModel):
    control_code = TextField()
    time = DoubleField()


class Result(BaseModel):
    start = ForeignKeyField(Start)
    finish_time = DateTimeField()
    status = ForeignKeyField(ResultStatus)
    split_time = ForeignKeyField(SplitTime)
    control_card = ForeignKeyField(ControlCard)
