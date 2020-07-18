from typing import List, Optional
from datetime import date
from enum import Enum

from pydantic import BaseModel


class RaceType(str, Enum):
    INDIVIDUAL_RACE = 'INDIVIDUAL_RACE'
    RELAY = 'RELAY'


class Status(str, Enum):
    NONE = 'NONE'
    OK = 'OK'
    FINISHED = 'FINISHED'
    DISQUALIFIED = 'DISQUALIFIED'
    MISSING_PUNCH = 'MISSING_PUNCH'
    DID_NOT_FINISH = 'DID_NOT_FINISH'
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'
    OVERTIME = 'OVERTIME'
    SPORTING_WITHDRAWAL = 'SPORTING_WITHDRAWAL'
    NOT_COMPETING = 'NOT_COMPETING'
    MOVED = 'MOVED'
    MOVED_UP = 'MOVED_UP'
    DID_NOT_START = 'DID_NOT_START'
    DID_NOT_ENTER = 'DID_NOT_ENTER'
    CANCELLED = 'CANCELLED'
    RESTORED = 'RESTORED'


class Organization(BaseModel):
    id: str
    name: str
    country: str
    region: str
    contact: str
    count_person: int


class Course(BaseModel):
    id: str
    name: str
    length: float
    climb: float
    controls: List[str]
    corridor: int
    count_person: int
    count_group: int


class Group(BaseModel):
    id: str
    name: str
    long_name: str
    start_interval: int
    start_corridor: int
    order_in_corridor: int
    first_number: int
    ranking: str
    type: Optional[RaceType]
    relay_legs: int
    count_person: int
    count_finished: int


class Split(BaseModel):
    code: str
    absolute_time: int


class Competitor(BaseModel):
    id: str
    name: str
    surname: str
    bib: int
    leg: int = 0
    group: Optional[Group]
    course: Optional[Course]
    is_out_of_competition: bool = False
    comment: str
    birthday: date
    start_time: int
    finish_time: int
    splits: List[Split]
    place: int
    status: Status


class Settings(BaseModel):
    title: str
    date: date
    type: RaceType


class Race(BaseModel):
    id: str
    organizations: List[Organization]
    groups: List[Group]
    courses: List[Course]
    competitors: List[Competitor]
    settings: Settings

