from peewee import *

db = SqliteDatabase('data/database.sqlite')


class BaseModel(Model):
    class Meta:
        database = db


class Extensions(BaseModel):
    Name = TextField()
    Value = TextField()


class Id(BaseModel):
    Id = TextField()


class EventStatus(BaseModel):
    pass


class BaseMessageElement(BaseModel):
    pass


class CompetitorList(BaseModel):
    pass


class OrganisationList(BaseModel):
    pass


class ClassList(BaseModel):
    pass


class EntryList(BaseModel):
    pass


class CourseData(BaseModel):
    pass


class StartList(BaseModel):
    pass


class ServiceRequestList(BaseModel):
    pass


class ControlCardList(BaseModel):
    pass


class Competitor(BaseModel):
    pass


class ControlCard(BaseModel):
    Name = TextField()
    Value = TextField()


class Score(BaseModel):
    pass


class Organisation(BaseModel):
    pass


class EventForm(BaseModel):
    pass


class Race(BaseModel):
    pass


class EventClassification(BaseModel):
    pass


class RaceDiscipline(BaseModel):
    pass


class EventURL(BaseModel):
    EventURL = TextField()


class Schedule(BaseModel):
    pass


class InformationItem(BaseModel):
    pass


class Class(BaseModel):
    pass


class ClassType(BaseModel):
    pass


class EventClassStatus(BaseModel):
    pass


class RaceClassStatus(BaseModel):
    pass


class Fee(BaseModel):
    pass


class AssignedFee(BaseModel):
    pass


class Amount(BaseModel):
    pass


class PersonEntry(BaseModel):
    pass


class TeamEntry(BaseModel):
    pass


class TeamEntryPerson(BaseModel):
    pass


class StartTimeAllocationRequest(BaseModel):
    pass


class ClassStart(BaseModel):
    pass


class StartName(BaseModel):
    pass


class PersonStart(BaseModel):
    pass


class PersonRaceStart(BaseModel):
    pass


class TeamStart(BaseModel):
    pass


class TeamMemberStart(BaseModel):
    pass


class TeamMemberRaceStart(BaseModel):
    pass


class TeamResult(BaseModel):
    pass


class TeamMemberResult(BaseModel):
    pass


class TeamMemberRaceResult(BaseModel):
    pass


class OverallResult(BaseModel):
    pass


class ResultStatus(BaseModel):
    Name = TextField()
    Value = TextField()


class ControlAnswer(BaseModel):
    Answer = TextField()
    CorrectAnswer = TextField()
    Time = DoubleField()
    Extensions = ForeignKeyField(Extensions)


class SplitTime(BaseModel):
    ControlCode = TextField()
    Time = DoubleField()
    Extensions = ForeignKeyField(Extensions)


class Route(BaseModel):
    pass


class Leg(BaseModel):
    pass


class Control(BaseModel):
    pass


class GeoPosition(BaseModel):
    pass


class Map(BaseModel):
    pass


class Image(BaseModel):
    pass


class MapPosition(BaseModel):
    pass


class RaceCourseData(BaseModel):
    pass


class ClassCourseAssignment(BaseModel):
    pass


class PersonCourseAssignment(BaseModel):
    pass


class TeamCourseAssignment(BaseModel):
    pass


class TeamMemberCourseAssignment(BaseModel):
    pass


class Course(BaseModel):
    pass


class SimpleCourse(BaseModel):
    pass


class SimpleRaceCourse(BaseModel):
    pass


class CourseControl(BaseModel):
    pass


class Service(BaseModel):
    pass


class OrganisationServiceRequest(BaseModel):
    pass


class PersonServiceRequest(BaseModel):
    pass


class ServiceRequest(BaseModel):
    pass


class Account(BaseModel):
    Account = TextField()


class Country(BaseModel):
    Country = TextField()


class Contact(BaseModel):
    Name = TextField()
    Value = TextField()


class LanguageString(BaseModel):
    LanguageString = TextField()


class Address(BaseModel):
    CareOf = TextField()
    Street = TextField()
    ZipCode = TextField()
    City = TextField()
    State = TextField()
    Country = ForeignKeyField(Country)


class PersonName(BaseModel):
    Family = TextField()
    Given = TextField()


class Person(BaseModel):
    Id = ForeignKeyField(Id)
    Name = ForeignKeyField(PersonName)
    BirthDate = DateField()
    Nationality = ForeignKeyField(Country)
    Address = ForeignKeyField(Address)
    Contact = ForeignKeyField(Contact)
    Extensions = ForeignKeyField(Extensions)


class Role(BaseModel):
    Person = ForeignKeyField(Person)


class EntryReceiver(BaseModel):
    Address = ForeignKeyField(Address)
    Contact = ForeignKeyField(Contact)


class Event(BaseModel):
    Id = ForeignKeyField(Id)
    Name = TextField()
    StartTime = DateTimeField()
    EndTime = DateTimeField()
    Status = ForeignKeyField(EventStatus)
    Classification = ForeignKeyField(EventClassification)
    Form = ForeignKeyField(EventForm)
    Organiser = ForeignKeyField(Organisation)
    Official = ForeignKeyField(Role)
    Class = ForeignKeyField(Class)
    Race = ForeignKeyField(Race)
    EntryReceiver = ForeignKeyField(EntryReceiver)
    Service = ForeignKeyField(Service)
    Account = ForeignKeyField(Account)
    URL = ForeignKeyField(EventURL)
    Information = ForeignKeyField(InformationItem)
    Schedule = ForeignKeyField(Schedule)
    Extensions = ForeignKeyField(Extensions)


class PersonResult(BaseModel):
    EntryId = ForeignKeyField(Id)
    Person = ForeignKeyField(Person)
    Organisation = ForeignKeyField(Organisation)
    Extensions = ForeignKeyField(Extensions)


class ClassResult(BaseModel):
    Class = ForeignKeyField(Class)
    Course = ForeignKeyField(SimpleRaceCourse)
    PersonResult = ForeignKeyField(PersonResult)
    TeamResult = ForeignKeyField(TeamResult)
    Extensions = ForeignKeyField(Extensions)


class ResultList(BaseModel):
    Event = ForeignKeyField(Event)
    ClassResult = ForeignKeyField(ClassResult)
    Extensions = ForeignKeyField(Extensions)


class EventList(BaseModel):
    Event = ForeignKeyField(Event)
    Extensions = ForeignKeyField(Extensions)


class RaceClass(BaseModel):
    PunchingSystem = TextField()
    Fee = ForeignKeyField(Fee)
    FirstStart = DateTimeField()
    Status = ForeignKeyField(RaceClassStatus)
    Course = ForeignKeyField(SimpleCourse)
    OnlineControl = ForeignKeyField(Control)
    Extensions = ForeignKeyField(Extensions)


class PersonRaceResult(BaseModel):
    BibNumber = TextField()
    StartTime = DateTimeField()
    FinishTime = DateTimeField()
    Time = DoubleField()
    TimeBehind = DoubleField()
    Position = IntegerField()
    Status = ForeignKeyField(ResultStatus)
    Score = ForeignKeyField(Score)
    Course = ForeignKeyField(SimpleCourse)
    SplitTime = ForeignKeyField(SplitTime)
    ControlAnswer = ForeignKeyField(ControlAnswer)
    Route = ForeignKeyField(Route)
    ControlCard = ForeignKeyField(ControlCard)
    AssignedFee = ForeignKeyField(AssignedFee)
    ServiceRequest = ForeignKeyField(ServiceRequest)
    Extensions = ForeignKeyField(Extensions)
