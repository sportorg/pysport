import datetime
import logging
import re
import time
import uuid
from abc import ABC, abstractmethod
from datetime import date
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional

import dateutil.parser

from sportorg.common.model import Model
from sportorg.common.otime import OTime, TimeRounding
from sportorg.language import translate
from sportorg.modules.configs.configs import Config
from sportorg.utils.time import hhmmss_to_time, date_to_ddmmyyyy


class NotEmptyException(Exception):
    pass


class Limit:
    BIB = 100000
    PRICE = 100000000


class SystemType(Enum):
    NONE = 0
    MANUAL = 1
    SPORTIDENT = 2
    SFR = 3
    SPORTIDUINO = 4
    RFID_IMPINJ = 5
    SRPID = 6

    def __str__(self) -> str:
        return self._name_

    def __repr__(self) -> str:
        return self.__str__()


class _TitleType(Enum):
    def __str__(self) -> str:
        return self._name_

    def __repr__(self) -> str:
        return self.__str__()

    def get_title(self):
        return translate(str(self).lower().capitalize().replace("_", " "))

    @classmethod
    def get_titles(cls):
        ret = [obj.get_title() for obj in cls]
        return ret

    @classmethod
    def get_by_name(cls, printable_name):
        for obj in cls:
            if obj.get_title() == printable_name:
                return obj


class RaceType(_TitleType):
    INDIVIDUAL_RACE = 0
    # MASS_START = 1
    PURSUIT = 2
    RELAY = 3
    # ONE_MAN_RELAY = 4
    # SPRINT_RELAY = 5
    MULTI_DAY_RACE = 6


class ResultStatus(_TitleType):
    NONE = 0
    OK = 1
    FINISHED = 2
    DISQUALIFIED = 3
    MISSING_PUNCH = 4
    DID_NOT_FINISH = 5
    ACTIVE = 6
    INACTIVE = 7
    OVERTIME = 8
    SPORTING_WITHDRAWAL = 9
    NOT_COMPETING = 10
    MOVED = 11
    MOVED_UP = 12
    DID_NOT_START = 13
    DID_NOT_ENTER = 14
    CANCELLED = 15
    RESTORED = 16
    MISS_PENALTY_LAP = 17
    MULTI_DAY_ISSUE = 18


class Organization(Model):
    def __init__(self):
        self.id = uuid.uuid4()
        self.name = ""
        self.country = ""
        self.region = ""
        self.contact = ""
        self.code = ""
        self.count_person = 0
        self.count_finished = 0

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return "Organization {}".format(self.name)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "object": self.__class__.__name__,
            "id": str(self.id),
            "name": self.name,
            "country": self.country,
            "region": (
                self.region[3:]
                if self.region and len(self.region) > 3 and self.region[2] == "_"
                else self.region
            ),
            "contact": self.contact,
            "code": self.code,
            "count_person": self.count_person,  # readonly
            "sex": 0,
        }

    def update_data(self, data: Dict[str, Any]) -> None:
        self.name = str(data["name"]) if "name" in data else ""
        self.country = str(data["country"]) if "country" in data else ""
        self.region = str(data["region"]) if "region" in data else ""
        self.code = str(data["code"]) if "code" in data else ""
        self.contact = str(data["contact"]) if "contact" in data else ""


class CourseControl(Model):
    def __init__(self):
        self.code = ""
        self.length = 0
        self.order = 0

    def __str__(self) -> str:
        return "{} {}".format(self.code, self.length)

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other) -> bool:
        return self.code == other.code

    def get_number_code(self) -> str:
        """Get control code (number as string)
        31 933 -> 31
        31(31,32,33) 933 -> 31
        * -> 0
        % -> 0
        """
        if not self.code:
            return "0"

        tmp = str(self.code)
        char = tmp[0]
        if char == "*" or char == "%":
            return "0"
        res = ""

        index = 0
        while char.isdigit() and index <= len(tmp) - 1:
            res += char
            index += 1
            if index < len(tmp):
                char = tmp[index]
        return str(res)

    def to_dict(self):
        return {
            "object": self.__class__.__name__,
            "code": self.code,
            "length": self.length,
        }

    def update_data(self, data):
        self.code = str(data["code"])
        self.length = int(data["length"])


class ControlPoint(Model):
    """Description of independent control point. Used for score calculation in rogain"""

    def __init__(self):
        self.code = ""
        self.description = ""
        self.score = 1.0
        self.x = 0.0
        self.y = 0.0
        self.altitude = 0.0


class Course(Model):
    def __init__(self):
        self.id = uuid.uuid4()
        self._name = ""
        self.bib = 0
        self.length = 0
        self.climb = 0
        self.controls: List[CourseControl] = []

        self.count_person = 0
        self.count_group = 0
        self.corridor = 0

        self.count_person = 0
        self.count_finished = 0

    def __repr__(self) -> str:
        return "Course {} {}".format(self.name, repr(self.controls))

    def __eq__(self, other) -> bool:
        if len(self.controls) != len(other.controls):
            return False
        for i in range(len(self.controls)):
            if self.controls[i] != other.controls[i]:
                return False

        return True

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_name: str):
        self._set_name(new_name)

    def is_unknown(self):
        for control in self.controls:
            if "*" in control.code or "%" in control.code or "(" in control.code:
                return True

        return False

    def get_code_list(self):
        ret = []
        for i in self.controls:
            ret.append(str(i.code))
        return ret

    def to_dict(self):
        controls = [control.to_dict() for control in self.controls]
        return {
            "object": self.__class__.__name__,
            "id": str(self.id),
            "controls": controls,
            "bib": self.bib,
            "name": self.name,
            "length": self.length,
            "climb": self.climb,
            "corridor": self.corridor,
        }

    def update_data(self, data):
        self.name = str(data["name"])
        self.bib = int(data["bib"])
        self.length = int(data["length"])
        self.climb = int(data["climb"])
        self.corridor = int(data["corridor"])
        self.controls = []
        for item in data["controls"]:
            control = CourseControl()
            control.update_data(item)
            self.controls.append(control)

    def index_name(self):
        self._set_name(self.name)

    def _set_name(self, new_name: str) -> None:
        r = race()

        # remove old name index
        if self.name != new_name and self.name in r.course_index_name:
            r.course_index_name.pop(self.name)

        if new_name in r.course_index_name:
            other_course = r.course_index_name[new_name]
            if other_course is not self:
                logging.info("Duplicate course name: %s", new_name)
        r.course_index_name[new_name] = self
        self._name = new_name


class Group(Model):
    def __init__(self):
        self.id = uuid.uuid4()
        self.name = ""
        self.course: Optional[Course] = None
        self.is_any_course = False
        self.price = 0
        self.long_name = ""

        self.min_year = 0
        self.max_year = 0

        self.min_age = 0
        self.max_age = 0

        self.max_time = OTime()
        self.start_interval = OTime()
        self.start_corridor = 0
        self.order_in_corridor = 0

        self.first_number = 0
        self.count_person = 0
        self.count_finished = 0
        self.pursuit_start_time = OTime()

        self.ranking = Ranking()
        self.__type: Optional[RaceType] = None
        self.is_best_team_placing_mode: bool = False
        self.relay_legs = 0

    def __repr__(self) -> str:
        return "Group {}".format(self.name)

    def get_count_finished(self):
        return self.count_finished

    def get_count_all(self):
        return self.count_person

    @property
    def race_type(self):
        return self.get_type()

    @race_type.setter
    def race_type(self, value):
        self.set_type(value)

    def get_type(self):
        if self.__type is not None:
            return self.__type
        return race().data.race_type

    def set_type(self, new_type):
        if self.__type == RaceType.RELAY and new_type != RaceType.RELAY:
            self.is_best_team_placing_mode = False
        self.__type = new_type

    def is_relay(self):
        return self.get_type() == RaceType.RELAY

    def to_dict(self):
        return {
            "object": self.__class__.__name__,
            "id": str(self.id),
            "name": self.name,
            "course_id": str(self.course.id) if self.course else None,
            "is_any_course": self.is_any_course,
            "long_name": self.long_name,
            "price": self.price,
            "min_year": self.min_year,
            "max_year": self.max_year,
            "min_age": self.min_age,
            "max_age": self.max_age,
            "max_time": self.max_time.to_msec(),
            "start_interval": self.start_interval.to_msec(),
            "start_corridor": self.start_corridor,
            "order_in_corridor": self.order_in_corridor,
            "first_number": self.first_number,
            "count_person": self.count_person,  # readonly
            "count_finished": self.count_finished,  # readonly
            "ranking": self.ranking.to_dict() if self.ranking else None,
            "__type": self.__type.value if self.__type is not None else None,
            "is_best_team_placing_mode": self.is_best_team_placing_mode,
            "relay_legs": self.relay_legs,
            "sex": 0,
        }

    def update_data(self, data):
        self.name = str(data["name"])
        self.long_name = str(data["long_name"])
        self.price = int(data["price"])
        self.min_year = int(data["min_year"])
        self.max_year = int(data["max_year"])
        self.min_age = int(data["min_age"])
        self.max_age = int(data["max_age"])
        self.max_time = OTime(msec=int(data["max_time"]))
        self.start_interval = OTime(msec=int(data["start_interval"]))
        self.start_corridor = int(data["start_corridor"])
        self.order_in_corridor = int(data["order_in_corridor"])
        self.first_number = int(data["first_number"])
        self.relay_legs = int(data["relay_legs"])
        if "ranking" in data:
            if data["ranking"]:
                self.ranking = Ranking()
                self.ranking.update_data(data["ranking"])
        if "is_any_course" in data:
            self.is_any_course = bool(data["is_any_course"])
        if data["__type"] is not None:
            self.__type = RaceType(int(data["__type"]))
        self.is_best_team_placing_mode = bool(
            data.get("is_best_team_placing_mode", False)
        )


class Split(Model):
    def __init__(self):
        self.index = 0
        self.course_index = -1
        self.code = ""
        self.days = 0
        self._time: OTime = OTime()
        self.leg_time: OTime = OTime()
        self.relative_time: OTime = OTime()
        self.leg_place = 0
        self.relative_place = 0
        self.is_correct = True
        self.has_penalty = False
        self.speed = ""
        self.length_leg = 0

    def __repr__(self) -> str:
        return self.code

    @property
    def time(self):
        return self._time

    @time.setter
    def time(self, value):
        if value is None:
            value = OTime()
        self._time = value

    def __eq__(self, other) -> bool:
        if self.code == 0 or other.code == 0:
            return False
        if self.time is None or other.time is None:
            return False
        return self.code == other.code and self.time == other.time

    def to_dict(self):
        return {
            "object": self.__class__.__name__,
            "days": self.days,
            "code": self.code,
            "time": self.time.to_msec() if self.time else None,
            "index": self.index,  # readonly
            "course_index": self.course_index + 1,  # readonly
            "leg_time": self.leg_time.to_msec() if self.leg_time else None,  # readonly
            "relative_time": (
                self.relative_time.to_msec() if self.relative_time else None
            ),  # readonly
            "leg_place": self.leg_place,  # readonly
            "relative_place": self.relative_place,  # readonly
            "is_correct": self.is_correct,
            "speed": self.speed,  # readonly
            "length_leg": self.length_leg,
        }

    def update_data(self, data):
        self.code = str(data["code"])
        if data["time"]:
            self._time = OTime(msec=data["time"])
        if "days" in data:
            self.days = int(data["days"])


def format_result(result, length):
    # Format result string, appending with spaces to have specified length
    # used in multi day result string filling
    # e.g. 12:00:12, 14 -> '12:00:12      '
    ret = ""
    if result is not None:
        if result.is_status_ok():
            ret = result.get_result_otime_current_day().to_str()
        else:
            ret = result.status_comment
    return (ret + " " * length)[0:length]


class Result(ABC):
    def __init__(self):
        self.id = uuid.uuid4()
        self.days = 0
        self.bib = 0
        self.start_time: Optional[OTime] = None
        self.finish_time: OTime = OTime.now()
        self.person: Optional[Person] = None
        self.status = ResultStatus.OK
        self.status_comment = ""
        self.penalty_time: Optional[OTime] = None
        self.credit_time: Optional[OTime] = None
        self.penalty_laps = 0  # count of penalty legs (marked route)
        self.place = 0
        self.scores = 0
        self.rogaine_score = 0
        self.rogaine_penalty = 0
        self.scores_ardf = 0
        self.assigned_rank = Qualification.NOT_QUALIFIED
        self.diff: Optional[OTime] = None  # readonly
        self.diff_scores = 0  # readonly
        self.created_at = time.time()
        self.speed = ""
        self.can_win_count = 0  # quantity of athletes who can win at current time
        self.final_result_time: Optional[OTime] = None  # real time, when nobody can win

        self.card_number = 0
        self.splits: List[Split] = []
        self.__start_time = None
        self.__finish_time = None

        self.current_result = (
            None  # Keep current day result (multi day), general result will have sum
        )
        self.qty_ok_days = 0  # Quantity of multi day finishes with OK status

        self.order = 0  # Order number, introduced in 1.6, needed for result templates to sort results correctly

    def __str__(self) -> str:
        return str(self.system_type)

    def __repr__(self) -> str:
        return f"Result {self.system_type} {self.status}"

    def __eq__(self, other) -> bool:
        eq = self.system_type and other.system_type

        if race().get_setting("result_processing_mode", "time") == "time":
            if self.get_start_time() and other.get_start_time():
                eq = eq and self.get_start_time() == other.get_start_time()
            if self.get_finish_time() and other.get_finish_time():
                eq = eq and self.get_finish_time() == other.get_finish_time()
            else:
                return False
        elif race().get_setting("result_processing_mode", "time") == "ardf":
            eq = eq and self.scores_ardf == other.scores_ardf
            if eq and self.get_start_time() and other.get_start_time():
                eq = eq and self.get_start_time() == other.get_start_time()
            if eq and self.get_finish_time() and other.get_finish_time():
                eq = eq and self.get_finish_time() == other.get_finish_time()
            else:
                return False
        else:  # process by score (rogain)
            eq = eq and self.rogaine_score == other.rogaine_score
            if eq and self.get_start_time() and other.get_start_time():
                eq = eq and self.get_start_time() == other.get_start_time()
            if eq and self.get_finish_time() and other.get_finish_time():
                eq = eq and self.get_finish_time() == other.get_finish_time()
            else:
                return False
        return bool(eq)

    def __gt__(self, other) -> bool:  # greater is worse
        if self.is_status_ok() != other.is_status_ok():
            return other.is_status_ok()
        elif self.status != other.status and not self.is_status_ok():
            # incorrect statuses sort
            return self.status.value > other.status.value

        if race().get_setting("result_processing_mode", "time") == "time":
            if (
                self.get_result_otime() == OTime()
                and other.get_result_otime() > OTime()
            ):
                return True
            if (
                self.get_result_otime() > OTime()
                and other.get_result_otime() == OTime()
            ):
                return False
            return self.get_result_otime() > other.get_result_otime()
        elif race().get_setting("result_processing_mode", "time") == "ardf":
            if self.scores_ardf == other.scores_ardf:
                return self.get_result_otime() > other.get_result_otime()
            else:
                return self.scores_ardf < other.scores_ardf
        else:  # process by score (rogain)
            if self.rogaine_score == other.rogaine_score:
                return self.get_result_otime() > other.get_result_otime()
            else:
                return self.rogaine_score < other.rogaine_score

    @property
    @abstractmethod
    def system_type(self) -> SystemType:
        pass

    def to_dict(self):
        accuracy = race().get_setting("time_accuracy", 0)
        return {
            "object": self.__class__.__name__,
            "id": str(self.id),
            "bib": self.bib,
            "system_type": self.system_type.value,
            "person_id": str(self.person.id) if self.person else None,
            "days": self.days,
            "start_time": self.start_time.to_msec() if self.start_time else None,
            "finish_time": self.finish_time.to_msec() if self.finish_time else None,
            "diff": self.diff.to_msec() if self.diff else None,
            "diff_scores": self.diff_scores,
            "penalty_time": self.penalty_time.to_msec() if self.penalty_time else None,
            "credit_time": self.credit_time.to_msec() if self.credit_time else None,
            "status": self.status.value,
            "status_comment": self.status_comment,
            "penalty_laps": self.penalty_laps,
            "place": self.place,
            "assigned_rank": self.assigned_rank.value,
            "splits": [split.to_dict() for split in self.splits],
            "card_number": self.card_number,
            "speed": self.speed,  # readonly
            "scores": self.scores,  # readonly
            "rogaine_score": self.rogaine_score,  # readonly
            "rogaine_penalty": self.rogaine_penalty,  # readonly
            "scores_ardf": self.scores_ardf,  # readonly
            "created_at": self.created_at,  # readonly
            "result": self.get_result(),  # readonly
            "result_relay": self.get_result_relay(),
            "result_current": (
                self.get_result_otime_current_day().to_str(time_accuracy=accuracy)
                if self.is_status_ok()
                else self.get_result()
            ),
            "start_msec": self.get_start_time().to_msec(),  # readonly
            "finish_msec": self.get_finish_time().to_msec(),  # readonly
            "result_msec": self.get_result_otime().to_msec(),  # readonly
            "result_relay_msec": self.get_result_otime_relay().to_msec(),  # readonly
            "result_current_msec": self.get_result_otime_current_day().to_msec(),  # readonly
            "can_win_count": self.can_win_count,
            "final_result_time": (
                self.final_result_time.to_str() if self.final_result_time else None
            ),
            "order": self.order,
            "multi_day_results": self.get_multi_day_result_str(),
        }

    def update_data(self, data):
        self.status = ResultStatus(int(data["status"]))
        self.penalty_laps = int(data["penalty_laps"])
        self.scores = data["scores"]
        if "scores_ardf" in data and data["scores_ardf"] is not None:
            self.scores_ardf = data["scores_ardf"]
        if "rogaine_score" in data and data["rogaine_score"] is not None:
            self.rogaine_score = data["rogaine_score"]
        if "rogaine_penalty" in data and data["rogaine_penalty"] is not None:
            self.rogaine_penalty = data["rogaine_penalty"]
        if str(data["place"]).isdigit():
            self.place = int(data["place"])
        self.assigned_rank = Qualification.get_qual_by_code(data["assigned_rank"])
        if data["start_time"] is not None:
            self.start_time = OTime(msec=data["start_time"])
        if data["finish_time"] is not None:
            self.finish_time = OTime(msec=data["finish_time"])
        if data["penalty_time"]:
            self.penalty_time = OTime(msec=data["penalty_time"])
        if "credit_time" in data and data["credit_time"] is not None:
            self.credit_time = OTime(msec=data["credit_time"])
        if "status_comment" in data:
            self.status_comment = data["status_comment"]
        if "days" in data:
            self.days = int(data["days"])
        if "created_at" in data:
            self.created_at = float(data["created_at"])
        else:
            self.created_at = time.time()

        if "bib" in data:
            self.bib = int(data["bib"])

        if "card_number" in data:
            self.card_number = int(data["card_number"])
        if "splits" in data:
            self.splits = []
            for item in data["splits"]:
                split = Split()
                split.update_data(item)
                self.splits.append(split)

    def clear(self) -> None:
        pass

    def get_bib(self) -> int:
        if self.person:
            return self.person.bib
        return self.bib

    def get_result(self) -> str:
        if not self.is_status_ok():
            if self.status_comment:
                return self.status_comment
            return self.status.get_title()

        if not self.person:
            return ""

        ret = ""
        if race().get_setting("result_processing_mode", "time") == "ardf":
            ret += f"{self.scores_ardf} {translate('points')} "
        elif race().get_setting("result_processing_mode", "time") == "scores":
            ret += f"{self.rogaine_score} {translate('points')} "

        time_accuracy = race().get_setting("time_accuracy", 0)
        ret += self.get_result_otime().to_str(time_accuracy)
        return ret

    def get_result_start_in_comment(self):
        if not self.is_status_ok():
            if self.status_comment:
                return self.status_comment
            return self.status.get_title()

        if not self.person:
            return ""

        ret = ""
        if race().get_setting("result_processing_mode", "time") == "ardf":
            ret += f"{self.scores_ardf} {translate('points')} "
        elif race().get_setting("result_processing_mode", "time") == "scores":
            ret += f"{self.rogaine_score} {translate('points')} "

        # time_accuracy = race().get_setting('time_accuracy', 0)
        start = hhmmss_to_time(self.person.comment)
        if start == OTime():
            raise ValueError
        ret += str(self.get_finish_time() - start)
        return ret

    def get_result_relay(self) -> str:
        if not self.is_status_ok():
            if self.status_comment:
                return self.status_comment
            return self.status.get_title()

        if not self.person:
            return ""

        # Check previous legs not to be disqualified
        if (
            self.person.bib > 2000
            and self.person.group
            and self.person.group.is_relay()
        ):
            cur_bib = self.person.bib - 1000
            while cur_bib > 1000:
                prev_person = race().find_person_by_bib(cur_bib)
                res = race().find_person_result(prev_person)
                if res and not res.is_status_ok():
                    return res.status.get_title()
                cur_bib -= 1000

        ret = ""
        if race().get_setting("result_processing_mode", "time") == "ardf":
            ret += f"{self.scores_ardf} {translate('points')} "
        elif race().get_setting("result_processing_mode", "time") == "scores":
            ret += f"{self.rogaine_score} {translate('points')} "

        time_accuracy = race().get_setting("time_accuracy", 0)
        ret += self.get_result_otime_relay().to_str(time_accuracy)
        return ret

    def get_result_for_sort(self):
        ret = self.get_result_otime()
        return self.status, ret.to_msec()

    def get_result_otime(self):
        race_type = RaceType.INDIVIDUAL_RACE
        if self.person and self.person.group:
            race_type = self.person.group.race_type

        if race_type == RaceType.INDIVIDUAL_RACE:
            return self.get_result_otime_current_day()
        if race_type == RaceType.MULTI_DAY_RACE:
            return self.get_result_otime_multi_day()
        if race_type == RaceType.RELAY:
            return self.get_result_otime_relay()

    def get_result_otime_current_day(self):
        time_accuracy = race().get_setting("time_accuracy", 0)
        time_rounding = race().get_setting("time_rounding", "math")
        ret_ms = self.get_finish_time().to_msec() - self.get_start_time().to_msec()
        ret_ms += self.get_penalty_time().to_msec()
        ret_ms -= self.get_credit_time().to_msec()
        return OTime(msec=ret_ms).round(time_accuracy, TimeRounding[time_rounding])

    def get_result_otime_relay(self):
        time_accuracy = race().get_setting("time_accuracy", 0)
        time_rounding = race().get_setting("time_rounding", "math")
        ret_ms = (
            self.get_finish_time().to_msec() - self.get_start_time_relay().to_msec()
        )

        # accumulate penalty for all legs
        ret_ms += self.get_penalty_time().to_msec()
        ret_ms -= self.get_credit_time().to_msec()

        if self.person:
            cur_bib = self.person.bib - 1000
            while cur_bib > 1000:
                prev_person = race().find_person_by_bib(cur_bib)
                res = race().find_person_result(prev_person)
                if res:
                    ret_ms += res.get_penalty_time().to_msec()
                    ret_ms -= res.get_credit_time().to_msec()
                cur_bib -= 1000

        return OTime(msec=ret_ms).round(time_accuracy, TimeRounding[time_rounding])

    def get_result_otime_multi_day(self):
        person_id = self.person.multi_day_id
        sum_result = OTime()
        for day in races():
            result_tmp = day.find_result_by_person_id(person_id)
            if result_tmp:
                if result_tmp.is_status_ok():
                    sum_result += result_tmp.get_result_otime_current_day()
                else:
                    self.status = ResultStatus.MULTI_DAY_ISSUE
                    self.status_comment = result_tmp.status_comment
                    return OTime()  # DSQ/DNS
            else:
                self.status = ResultStatus.MULTI_DAY_ISSUE
                return OTime()  # result not found in that day
        return sum_result

    def get_start_time(self):
        if self.person and self.person.group:
            group = self.person.group
            if group.get_type() == RaceType.PURSUIT:
                return group.pursuit_start_time

        if self.start_time and self.start_time.to_msec():
            return self.start_time
        if self.person and self.person.start_time and self.person.start_time.to_msec():
            return self.person.start_time
        return OTime()

    # Find the start time or relay team = start time of first leg
    def get_start_time_relay(self):
        if self.person:
            first_leg_person = self.person
            if (
                self.person.bib > 2000
                and self.person.group
                and self.person.group.is_relay()
            ):
                bib_to_find = 1000 + self.person.bib % 1000
                first_leg_person = race().find_person_by_bib(bib_to_find)
            if first_leg_person:
                if (
                    first_leg_person.start_time
                    and first_leg_person.start_time.to_msec()
                ):
                    return first_leg_person.start_time
        return OTime()

    def get_finish_time(self) -> OTime:
        if self.finish_time:
            return self.finish_time

        return OTime.now()

    def get_penalty_time(self) -> OTime:
        if self.penalty_time:
            return self.penalty_time
        return OTime()

    def get_credit_time(self) -> OTime:
        if self.credit_time:
            return self.credit_time
        return OTime()

    def get_place(self):
        """Returns text for place column in results"""
        if self.place > 0:
            return self.place
        if self.person and self.person.is_out_of_competition:
            return translate("o/c")
        return ""

    def get_course_splits(self, course=None):
        return []

    def check(self, course=None):
        return True

    def is_status_ok(self):
        return self.status == ResultStatus.OK or self.status == ResultStatus.RESTORED

    def is_punch(self):
        return (
            self.is_sportident()
            or self.is_sfr()
            or self.is_sportiduino()
            or self.is_rfid_impinj()
            or self.is_srpid()
        )

    def is_sportident(self):
        return self.system_type == SystemType.SPORTIDENT

    def is_sfr(self):
        return self.system_type == SystemType.SFR

    def is_sportiduino(self):
        return self.system_type == SystemType.SPORTIDUINO

    def is_rfid_impinj(self):
        return self.system_type == SystemType.RFID_IMPINJ

    def is_srpid(self):
        return self.system_type == SystemType.SRPID

    def is_manual(self):
        return self.system_type == SystemType.MANUAL

    def check_who_can_win(self):
        """Generate statistic about unfinished athletes in the group for current person.
        Calculate, how much people can win and at what time current result will be final (nobody can win).
        """
        if self.person and self.person.group:
            who_can_win_count = 0
            max_unfinished_start_time = OTime()

            for cur_person in race().get_persons_by_group(self.person.group):
                if cur_person.result_count == 0:
                    if not cur_person.is_out_of_competition:
                        if cur_person.start_time and self.person.start_time:
                            if cur_person.start_time > self.person.start_time:
                                if (
                                    self.get_result_otime()
                                    > OTime.now() - cur_person.start_time
                                ):
                                    who_can_win_count += 1
                                    max_unfinished_start_time = max(
                                        cur_person.start_time, max_unfinished_start_time
                                    )
                        else:
                            who_can_win_count += 1

            self.can_win_count = who_can_win_count
            self.final_result_time = max_unfinished_start_time + self.get_result_otime()

    def get_multi_day_result_str(self):
        ret = ""
        for cur_res in self.get_multi_days():
            ret += format_result(cur_res, 14)
        return ret

    def get_multi_days(self) -> List["Result"]:
        """
        Get list of multi day results, None if group type not Multi Day
        Returns:
            list[Result]:
        """
        ret = []
        if (
            self.person
            and self.person.group
            and self.person.group.get_type() == RaceType.MULTI_DAY_RACE
        ):
            person_id = self.person.multi_day_id
            for day in races():
                cur_res: Result = day.find_result_by_person_id(person_id)
                if cur_res:
                    ret.append(cur_res)
        return ret


class ResultManual(Result):
    system_type = SystemType.MANUAL


class ResultSportident(Result):
    system_type = SystemType.SPORTIDENT

    def __init__(self):
        super(ResultSportident, self).__init__()
        self.__start_time = None
        self.__finish_time = None

    def __repr__(self) -> str:
        splits = "\n".join(
            f"{split.code} — {split.length_leg}" for split in self.splits
        )

        person = self.person.full_name if self.person else ""
        return (
            f"Card: {self.card_number}\n"
            f"Start: {self.start_time}\n"
            f"Finish: {self.finish_time}\n"
            f"Person: {person}\n"
            "Splits:\n"
            f"{splits}"
        )

    def __eq__(self, other) -> bool:
        eq = self.card_number == other.card_number and super().__eq__(other)
        if len(self.splits) == len(other.splits):
            for i in range(len(self.splits)):
                eq = eq and self.splits[i].code == other.splits[i].code
                eq = eq and self.splits[i].time == other.splits[i].time
        else:
            return False
        return eq

    def get_start_time(self):
        obj = race()

        if self.person and self.person.group:
            group = self.person.group
            if group.get_type() == RaceType.PURSUIT:
                return group.pursuit_start_time

        start_source = obj.get_setting("system_start_source", "protocol")
        if start_source == "protocol":
            if (
                self.person
                and self.person.start_time
                and self.person.start_time.to_msec()
            ):
                return self.person.start_time
        elif start_source == "station":
            if self.start_time and self.start_time.to_msec():
                return self.start_time
            elif (
                self.person
                and self.person.start_time
                and self.person.start_time.to_msec()
            ):
                return self.person.start_time
        elif start_source == "cp":
            if self.__start_time:
                return self.__start_time
            if len(self.splits):
                start_cp_number = obj.get_setting("system_start_cp_number", 31)
                if start_cp_number in (0, -1):
                    self.__start_time = self.splits[0].time
                    return self.__start_time
                for split in self.splits:
                    if split.code == str(start_cp_number):
                        self.__start_time = split.time
                        return self.__start_time
        elif start_source == "gate":
            pass

        return OTime()

    def get_finish_time(self) -> OTime:
        obj = race()
        finish_source = obj.get_setting("system_finish_source", "station")
        if finish_source == "station":
            if self.finish_time:
                return self.finish_time
        elif finish_source == "cp":
            if self.__finish_time:
                return self.__finish_time
            if len(self.splits):
                finish_cp_number = obj.get_setting("system_finish_cp_number", 90)
                if finish_cp_number in (0, -1):
                    self.__finish_time = self.splits[-1].time
                    return self.__finish_time
                for split in reversed(self.splits):
                    if split.code == str(finish_cp_number):
                        self.__finish_time = split.time
                        return self.__finish_time
        elif finish_source == "beam":
            pass

        # return 0 to avoid incorrect results
        return OTime()

    def clear(self):
        self.__start_time = None
        self.__finish_time = None

    def get_course_splits(self, course=None):
        splits = []
        for split in self.splits:
            if split.is_correct:
                splits.append(split)
        return splits

    def check(self, course=None):
        obj = race()
        if not course:
            return super().check()
        controls = course.controls
        course_index = 0
        count_controls = len(controls)
        if count_controls == 0:
            return True

        # list of indexes, coincide with course, used for mixed course order
        recognized_indexes = []

        # invalidate all splits before check
        for i in self.splits:
            i.is_correct = False
            i.has_penalty = True
            i.course_index = -1

        ignore_punches_before_start = obj.get_setting(
            "ignore_punches_before_start", False
        )

        optional_controls_taken = set()

        for i in range(len(self.splits)):
            try:
                split = self.splits[i]

                # ignore splits before start (not cleaned card or unintentional punches before start)
                if ignore_punches_before_start and split.time < self.get_start_time():
                    continue

                template = str(controls[course_index].code)
                cur_code = split.code

                list_exists = False
                list_contains = False
                ind_begin = template.find("(")
                ind_end = template.find(")")
                if ind_begin > 0 and ind_end > 0:
                    list_exists = True
                    # any control from the list e.g. '%(31,32,35-45)'
                    arr = re.split(r"\s*,\s*", template[ind_begin + 1 : ind_end])
                    for cp in arr:
                        cp_range = re.split(r"\s*-\s*", cp)
                        if int(cur_code) == int(cp_range[0]):
                            list_contains = True
                        elif len(cp_range) > 1:
                            if int(cur_code) > int(cp_range[0]) and int(
                                cur_code
                            ) <= int(cp_range[len(cp_range) - 1]):
                                list_contains = True

                if template.find("%") > -1:
                    # non-unique control
                    if not list_exists or list_contains:
                        # any control '%' or '%(31,32,33)' or '31%'
                        split.is_correct = True
                        split.has_penalty = False
                        recognized_indexes.append(i)
                        split.course_index = course_index
                        course_index += 1

                elif template.find("*") > -1:
                    # unique control '*' or '*(31,32,33)' or '31*'
                    if list_exists and not list_contains:
                        # not in list
                        continue
                    # test previous splits
                    is_unique = True
                    course_index_current = -1
                    for j in range(i):
                        prev_split = self.splits[j]

                        if prev_split.is_correct:
                            course_index_current += 1

                        if prev_split.code == cur_code and j in recognized_indexes:
                            if (
                                course_index_current < 0
                                or str(controls[course_index_current].code).find("*")
                                < 0
                            ):
                                # check only free order controls to be duplicated
                                continue

                            is_unique = False
                            break
                    if is_unique:
                        split.is_correct = True
                        split.has_penalty = False
                        recognized_indexes.append(i)
                        split.course_index = course_index
                        course_index += 1

                elif template.find("?") > -1:
                    # optional control '?' or '?(31,32,33)' or '31?'
                    if cur_code in optional_controls_taken:
                        continue

                    if not list_exists or list_contains:
                        # any control '?' or '?(31,32,33)' or '31?'
                        split.is_correct = True
                        split.has_penalty = False
                        recognized_indexes.append(i)
                        optional_controls_taken.add(cur_code)
                        split.course_index = course_index

                else:
                    # simple pre-ordered control '31 989' or '31(31,32,33) 989'
                    if list_exists:
                        # control with optional codes '31(31,32,33) 989'
                        if list_contains:
                            split.is_correct = True
                            recognized_indexes.append(i)

                            correct_code = (
                                str(controls[course_index].code).split("(")[0].strip()
                            )
                            if split.code == correct_code:
                                split.has_penalty = False

                            split.course_index = course_index
                            course_index += 1
                    else:
                        # just cp '31 989'
                        is_equal = str(cur_code) == controls[course_index].code
                        if is_equal:
                            split.is_correct = True
                            split.has_penalty = False
                            recognized_indexes.append(i)
                            split.course_index = course_index
                            course_index += 1

                if course_index == count_controls:
                    return True

            except KeyError:
                return False

        return False

    def merge_with(self, new_result):
        # Merge with new result (merge splits, backup old finish/start, use new finish/start as finish/start)
        tolerance_sec = 10
        start_code = "10"
        finish_code = "20"

        is_changed = False

        # backup old start as punch
        if self.start_time and new_result.start_time and self.start_time > OTime():
            if (
                abs(new_result.start_time.to_sec() - self.start_time.to_sec())
                > tolerance_sec
            ):
                i = 0
                while i < len(self.splits) and self.splits[i].code == start_code:
                    i += 1
                backup_start = Split()
                backup_start.code = start_code
                backup_start.time = self.start_time
                self.splits.insert(i, backup_start)
                self.start_time = new_result.start_time
                is_changed = True

        # backup old finish as punch
        if self.finish_time and new_result.finish_time and self.finish_time > OTime():
            if (
                abs(new_result.finish_time.to_sec() - self.finish_time.to_sec())
                > tolerance_sec
            ):
                backup_finish = Split()
                backup_finish.time = self.finish_time
                backup_finish.code = finish_code
                self.splits.append(backup_finish)
                self.finish_time = new_result.finish_time
                is_changed = True

        # skip duplicated punches, then append different
        offset = 0
        for punch_new in new_result.splits:
            exists = False
            for punch_old in self.splits:
                if punch_new.code == punch_old.code:
                    if (
                        abs(punch_new.time.to_sec() - punch_old.time.to_sec())
                        < tolerance_sec
                    ):
                        exists = True
                        break
            if not exists:
                break
            offset += 1
        if offset < len(new_result.splits):
            is_changed = True
            for split in new_result.splits[offset:]:
                self.splits.append(split)

        return is_changed

    def sort_splits(self):
        self.splits.sort(key=lambda c: c.time)

    def remove_duplicated_splits(self):
        if len(self.splits) < 2:
            return
        for i in reversed(range(len(self.splits) - 1)):
            if self.splits[i] == self.splits[i + 1]:
                self.splits.remove(self.splits[i])


class ResultSFR(ResultSportident):
    system_type = SystemType.SFR


class ResultSportiduino(ResultSportident):
    system_type = SystemType.SPORTIDUINO


class ResultRfidImpinj(ResultSportident):
    system_type = SystemType.RFID_IMPINJ


class ResultSrpid(ResultSportident):
    system_type = SystemType.SRPID


class Person(Model):
    def __init__(self):
        self.id = uuid.uuid4()
        self.name = ""
        self.surname = ""
        self.middle_name = ""

        self._card_number = 0
        self._bib = 0

        self.birth_date: Optional[date] = None
        self.organization: Optional[Organization] = None
        self.group: Optional[Group] = None
        self.world_code = ""  # WRE ID for orienteering and the same
        self.national_code = 0
        self.qual: Qualification = Qualification.NOT_QUALIFIED
        self.is_out_of_competition = False  # e.g. 20-years old person, running in M12
        self.is_paid = False
        self.is_rented_card = False
        self.is_personal = False
        self.comment = ""

        self.start_time: OTime = OTime(0)
        self.start_group = 0
        self.result_count = 0

    def __repr__(self) -> str:
        return f"{self.full_name} {self.bib} {self.group}"

    @property
    def year(self):
        return self.get_year()

    @year.setter
    def year(self, value: int):
        self.set_year(value)

    def get_year(self):
        """Get year from birth_date. If only year is used in the event, it's stored as 01-01-year"""
        if self.birth_date:
            return self.birth_date.year
        return 0

    def get_birthday(self):
        if self.birth_date:
            return date_to_ddmmyyyy(self.birth_date)
        return ""

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
        ret = self.name
        if self.surname:
            ret = f"{self.surname} {ret}"
        return ret

    @property
    def full_name_with_middle(self):
        ret = self.name
        if self.middle_name:
            ret = f"{ret} {self.middle_name}"
        if self.surname:
            ret = f"{self.surname} {ret}"
        return ret

    @property
    def multi_day_id(self):
        if self.group:
            return f"{self.full_name} {self.group.name}"
        else:
            return self.full_name

    def to_dict(self):
        return {
            "object": self.__class__.__name__,
            "id": str(self.id),
            "name": self.name,
            "surname": self.surname,
            "middle_name": self.middle_name,
            "card_number": self.card_number,
            "bib": self.bib,
            "birth_date": str(self.birth_date) if self.birth_date else None,
            "year": (
                self.get_year() if self.get_year() else 0
            ),  # back compatibility with 1.0
            "birthday": self.get_birthday(),
            "group_id": str(self.group.id) if self.group else None,
            "organization_id": str(self.organization.id) if self.organization else None,
            "world_code": self.world_code,
            "national_code": self.national_code,
            "qual": self.qual.value,
            "is_out_of_competition": self.is_out_of_competition,
            "is_paid": self.is_paid,
            "is_rented_card": self.is_rented_card,
            "is_personal": self.is_personal,
            "comment": self.comment,
            "start_time": self.start_time.to_msec() if self.start_time else None,
            "start_group": self.start_group,
            "sex": 0,  # back compatibility with 1.5
        }

    def update_data(self, data):
        self.name = str(data["name"])
        self.surname = str(data["surname"])
        if "middle_name" in data and data["middle_name"]:
            self.middle_name = str(data["middle_name"])
        self.set_card_number(int(data["card_number"]))
        self.set_bib(int(data["bib"]))
        self.contact = []
        if data["world_code"]:
            self.world_code = str(data["world_code"])
        if data["national_code"]:
            self.national_code = data["national_code"]
        self.qual = Qualification.get_qual_by_code(data["qual"])
        self.is_out_of_competition = bool(data["is_out_of_competition"])
        self.is_paid = bool(data["is_paid"])
        self.is_rented_card = bool(data["is_rented_card"])
        self.is_personal = bool(data["is_personal"])
        self.comment = str(data["comment"])
        self.start_group = int(data["start_group"])
        if data["start_time"]:
            self.start_time = OTime(msec=int(data["start_time"]))
        if data["birth_date"]:
            self.birth_date = dateutil.parser.parse(data["birth_date"]).date()
        elif "year" in data and data["year"]:  # back compatibility with v 1.0.0
            self.set_year(int(data["year"]))

    @property
    def bib(self):
        return self._bib

    @bib.setter
    def bib(self, new_bib: int):
        raise NotImplementedError("Please, use set_bib()")

    def set_bib(self, new_bib: int) -> None:
        if self._bib == new_bib:
            return
        self._index_bib(new_bib)
        self._bib = new_bib

    # used for duplication
    def set_bib_without_indexing(self, new_bib: int) -> None:
        self._bib = new_bib

    def _index_bib(self, new_bib: int) -> None:
        r = race()
        if self._bib != new_bib and self._bib in r.person_index_bib:
            r.person_index_bib.pop(self.bib)
        if new_bib > 0 and new_bib in r.person_index_bib:
            other_person = r.person_index_bib[new_bib]
            if other_person is not self:
                logging.info(
                    "Duplicate bib %s: %s (indexed) | %s (not indexed)",
                    new_bib,
                    self,
                    other_person,
                )
        r.person_index_bib[new_bib] = self

    def index_bib(self) -> None:
        self._index_bib(self.bib)

    @property
    def card_number(self):
        return self._card_number

    @card_number.setter
    def card_number(self, new_card: int):
        raise NotImplementedError("Please, use set_card_number()")

    def set_card_number(self, new_card: int):
        if self._card_number == new_card:
            return

        self._index_card(new_card)
        self._card_number = new_card

    # used for duplication
    def set_card_number_without_indexing(self, new_card: int):
        self._card_number = new_card

    def _index_card(self, new_card):
        r = race()
        if self._card_number != new_card and self._card_number in r.person_index_card:
            r.person_index_card.pop(self._card_number)
        if new_card > 0 and new_card in r.person_index_card:
            other_person = r.person_index_card[new_card]
            if other_person is not self:
                logging.info(
                    "Duplicate card %s: %s (indexed) | %s (not indexed)",
                    new_card,
                    self,
                    other_person,
                )
        r.person_index_card[new_card] = self

    def index_card(self):
        self._index_card(self._card_number)

    def extract_middle_name(self):
        arr = self.name.split(" ", 1)
        if len(arr) > 1:
            self.name = arr[0]
            self.middle_name = arr[1]


class RaceData(Model):
    def __init__(self):
        self.title = ""
        self.description = ""
        self.location = ""
        self.chief_referee = ""
        self.secretary = ""
        self.url = ""
        self.race_type = RaceType.INDIVIDUAL_RACE
        self.start_datetime: Optional[datetime.datetime] = None
        self.end_datetime: Optional[datetime.datetime] = None
        self.relay_leg_count = 3

    def __repr__(self) -> str:
        return "Race {}".format(self.title)

    def get_start_datetime(self):
        if self.start_datetime is None:
            return datetime.datetime.now().replace(second=0, microsecond=0)
        return self.start_datetime

    def get_end_datetime(self):
        if self.end_datetime is None:
            return datetime.datetime.now().replace(second=0, microsecond=0)
        return self.end_datetime

    def get_days(self, date_=None):
        if self.start_datetime is None:
            return 0
        if date_ is None:
            date_ = datetime.datetime.now()
        return max((date_ - self.start_datetime).days, 0)

    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "chief_referee": self.chief_referee,
            "secretary": self.secretary,
            "url": self.url,
            "race_type": self.race_type.value,
            "start_datetime": str(self.start_datetime) if self.start_datetime else None,
            "end_datetime": str(self.end_datetime) if self.end_datetime else None,
            "relay_leg_count": self.relay_leg_count,
        }

    def update_data(self, data):
        self.title = str(data["title"])
        self.description = str(data["description"])
        self.location = str(data["location"])
        self.chief_referee = str(data["chief_referee"])
        self.secretary = str(data["secretary"])
        self.url = str(data["url"])
        self.race_type = RaceType(int(data["race_type"]))
        self.relay_leg_count = int(data["relay_leg_count"])
        if data["start_datetime"]:
            self.start_datetime = dateutil.parser.parse(data["start_datetime"])
        if data["end_datetime"]:
            self.end_datetime = dateutil.parser.parse(data["end_datetime"])


class Race(Model):
    support_obj = {
        "Person": Person,
        "Result": Result,
        "ResultManual": ResultManual,
        "ResultSportident": ResultSportident,
        "ResultSFR": ResultSFR,
        "ResultSportiduino": ResultSportiduino,
        "ResultRfidImpinj": ResultRfidImpinj,
        "ResultSrpid": ResultSrpid,
        "Group": Group,
        "Course": Course,
        "Organization": Organization,
    }

    def __init__(self):
        self.id = uuid.uuid4()
        self.data = RaceData()
        self.organizations: List[Organization] = []
        self.courses: List[Course] = []
        self.groups: List[Group] = []
        self.results: List[Result] = []
        self.persons: List[Person] = []
        self.relay_teams: List[RelayTeam] = []
        self.settings: Dict[str, Any] = {}
        self.controls: List[ControlPoint] = []
        self.result_index: Dict[str, Result] = {}
        self.person_index_bib: Dict[int, Person] = {}
        self.person_index_card: Dict[int, Person] = {}
        self.person_index: Dict[str, Result] = {}
        self.group_index: Dict[str, Group] = {}
        self.organization_index: Dict[str, Organization] = {}
        self.course_index: Dict[str, Course] = {}
        self.course_index_name: Dict[str, Course] = {}

    def __repr__(self) -> str:
        return repr(self.data)

    @property
    def list_obj(self):
        return {
            "Person": self.persons,
            "Result": self.results,
            "ResultManual": self.results,
            "ResultSportident": self.results,
            "ResultSFR": self.results,
            "ResultSportiduino": self.results,
            "ResultRfidImpinj": self.results,
            "ResultSrpid": self.results,
            "Group": self.groups,
            "Course": self.courses,
            "Organization": self.organizations,
        }

    @property
    def index_obj(self):
        return {
            "Person": self.person_index,
            "Result": self.result_index,
            "ResultManual": self.result_index,
            "ResultSportident": self.result_index,
            "ResultSFR": self.result_index,
            "ResultSportiduino": self.result_index,
            "ResultRfidImpinj": self.result_index,
            "ResultSrpid": self.result_index,
            "Group": self.group_index,
            "Course": self.course_index,
            "Organization": self.organization_index,
        }

    def to_dict(self):
        return {
            "object": self.__class__.__name__,
            "id": str(self.id),
            "data": self.data.to_dict(),
            "settings": self.settings,
            "organizations": [item.to_dict() for item in self.organizations],
            "courses": [item.to_dict() for item in self.courses],
            "groups": [item.to_dict() for item in self.groups],
            "results": [item.to_dict() for item in self.results],
            "persons": [item.to_dict() for item in self.persons],
        }

    def to_dict_partial(
        self,
        person_list=[],
        group_list=[],
        course_list=[],
        orgs_list=[],
        result_list=[],
    ):
        if course_list and len(course_list) > 0:
            for group in self.groups:
                if group.course and group.course in course_list:
                    group_list.append(group.name)

        if group_list and len(group_list) > 0:
            for person in self.persons:
                if (
                    person.group
                    and person.group.name in group_list
                    and person not in person_list
                ):
                    person_list.append(person)

        if orgs_list and len(orgs_list) > 0:
            person_list = []
            for person in self.persons:
                if (
                    person.organization
                    and person.organization in orgs_list
                    and person not in person_list
                ):
                    person_list.append(person)

        if result_list and len(result_list) > 0:
            person_list = []
            for result in result_list:
                if result.person and result.person not in person_list:
                    person_list.append(result.person)

        if person_list and len(person_list) > 0:
            # person list to filter specified
            return_groups = set()
            return_orgs = set()
            return_results = list()
            return_courses = list()
            for person in person_list:
                if person.group:
                    return_groups.add(person.group)
                if person.organization:
                    return_orgs.add(person.organization)
            for group in return_groups:
                if group.course and group.course not in return_courses:
                    return_courses.append(group.course)
            for result in self.results:
                if result.person in person_list:
                    return_results.append(result)

            # person list to filter specified
            return_groups = set()
            return_orgs = set()
            return_results = list()
            return_courses = list()
            for person in person_list:
                if person.group:
                    return_groups.add(person.group)
                if person.organization:
                    return_orgs.add(person.organization)
            for group in return_groups:
                if group.course and group.course not in return_courses:
                    return_courses.append(group.course)
            for result in self.results:
                if result.person in person_list:
                    return_results.append(result)

            return {
                "object": self.__class__.__name__,
                "id": str(self.id),
                "data": self.data.to_dict(),
                "settings": self.settings,
                "organizations": [item.to_dict() for item in return_orgs],
                "courses": [item.to_dict() for item in return_courses],
                "groups": [item.to_dict() for item in return_groups],
                "results": [item.to_dict() for item in return_results],
                "persons": [item.to_dict() for item in person_list],
            }
        return None

    def update_data(self, dict_obj):
        if "object" not in dict_obj:
            return
        if dict_obj["object"] == "Race" and dict_obj["id"] == str(self.id):
            if "data" in dict_obj:
                self.data.update_data(dict_obj["data"])
            if "settings" in dict_obj:
                self.settings = dict_obj["settings"]
            key_list = ["organizations", "courses", "groups", "persons", "results"]
            for key in key_list:
                if key in dict_obj:
                    for item_obj in dict_obj[key]:
                        self.update_data(item_obj)
            return
        elif dict_obj["object"] not in self.support_obj:
            return

        obj = self.get_obj(dict_obj["object"], dict_obj["id"])
        if obj is None:
            self.create_obj(dict_obj)
        else:
            self.update_obj(obj, dict_obj)

    def get_obj(self, obj_name, obj_id):
        cur_dict = self.index_obj[obj_name]
        if obj_id in cur_dict:
            return cur_dict[obj_id]

    def update_obj(self, obj, dict_obj):
        obj.update_data(dict_obj)
        if dict_obj["object"] == "Person":
            obj.group = self.get_obj("Group", dict_obj["group_id"])
            obj.organization = self.get_obj("Organization", dict_obj["organization_id"])
        elif dict_obj["object"] in [
            "Result",
            "ResultManual",
            "ResultSportident",
            "ResultSFR",
            "ResultSportiduino",
            "ResultRfidImpinj",
            "ResultSrpid",
        ]:
            obj.person = self.get_obj("Person", dict_obj["person_id"])
        elif dict_obj["object"] == "Group":
            obj.course = self.get_obj("Course", dict_obj["course_id"])

    def create_obj(self, dict_obj):
        obj = self.support_obj[dict_obj["object"]]()
        obj.id = uuid.UUID(dict_obj["id"])
        self.update_obj(obj, dict_obj)
        self.list_obj[dict_obj["object"]].insert(0, obj)
        self.index_obj[dict_obj["object"]][dict_obj["id"]] = obj

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

    def get_days(self, date_=None):
        return self.data.get_days(date_)

    def person_card_number(self, person: Person, number=0):
        person.set_card_number(number)
        for p in self.persons:
            if p.card_number == number and p != person:
                p.set_card_number(0)
                p.is_rented_card = False
                return p

    def rebuild_indexes(self, rebuild_person=True, rebuild_course=False):
        if rebuild_person:
            self.person_index_bib = {}
            self.person_index_card = {}
            for person in self.persons:
                person.index_bib()
                person.index_card()

        if rebuild_course:
            self.course_index_name = {}
            for course in self.courses:
                course.index_name()

    def delete_persons(self, indexes):
        indexes = sorted(indexes, reverse=True)
        persons = []
        for i in indexes:
            person = self.persons[i]
            persons.append(person)
            self.remove_person_from_indexes(person)
            del self.persons[i]
        return persons

    def remove_person_from_indexes(self, person: Person):
        for result in self.results:
            if result.person is person:
                result.person = None
                result.bib = person.bib
        if (
            person.bib
            and person.bib in self.person_index_bib
            and self.person_index_bib[person.bib] is person
        ):
            del self.person_index_bib[person.bib]
        if (
            person.card_number
            and person.card_number in self.person_index_card
            and self.person_index_card[person.card_number] is person
        ):
            del self.person_index_card[person.card_number]

    def delete_results(self, indexes):
        indexes = sorted(indexes, reverse=True)
        results = []
        for i in indexes:
            result = self.results[i]
            results.append(result)
            del self.results[i]
        return results

    def delete_groups(self, indexes: List[int]) -> List[Group]:
        groups = []
        for i in indexes:
            group = self.groups[i]
            if group.count_person > 0:
                raise NotEmptyException("Cannot remove group")
            groups.append(group)

        indexes = sorted(indexes, reverse=True)
        for i in indexes:
            del self.groups[i]
        return groups

    def delete_courses(self, indexes: List[int]) -> List[Course]:
        courses = []
        for i in indexes:
            course = self.courses[i]
            if course.count_group > 0:
                raise NotEmptyException("Cannot remove course")
            courses.append(course)

        indexes = sorted(indexes, reverse=True)
        for i in indexes:
            del self.courses[i]
        return courses

    def delete_organizations(self, indexes: List[int]) -> List[Organization]:
        organizations = []
        for i in indexes:
            organization = self.organizations[i]
            if organization.count_person > 0:
                raise NotEmptyException("Cannot remove organization")
            organizations.append(organization)
        indexes = sorted(indexes, reverse=True)

        for i in indexes:
            del self.organizations[i]
        return organizations

    def find_person_result(self, person: Person) -> Optional[Result]:
        for i in self.results:
            if i.person is person:
                return i
        return None

    def find_person_by_bib(self, bib: int) -> Person:
        if bib in self.person_index_bib:
            return self.person_index_bib[bib]
        return None

    def find_person_by_card(self, card: int) -> Person:
        if card in self.person_index_card:
            return self.person_index_card[card]
        return None

    def find_course(self, result: Result) -> Optional[Course]:
        # first get course by number
        person = result.person
        if not person:
            return None

        bib = person.bib

        # use cache
        obj = race()

        if str(bib) in obj.course_index_name:
            return obj.course_index_name[str(bib)]

        bib_with_dot = ""
        if bib > 1000:
            bib_with_dot = str(bib % 1000) + "." + str(bib // 1000)
        if bib_with_dot in obj.course_index_name:
            return obj.course_index_name[bib_with_dot]

        ret = find(self.courses, name=str(bib))
        if not ret and bib > 1000:
            course_name = "{}.{}".format(bib % 1000, bib // 1000)
            ret = find(self.courses, name=course_name)
        # usual connection via group
        if not ret and person.group:
            if person.group.is_any_course:
                for course in self.courses:
                    if result.check(course):
                        return course
            else:
                ret = person.group.course
        return ret

    def find_group(self, group_name):
        # get group by name
        ret = find(self.groups, name=str(group_name))
        return ret

    def find_organization(self, org_name):
        # get organization by name
        ret = find(self.organizations, name=str(org_name))
        return ret

    def find_team(self, team_name):
        return self.find_organization(team_name)

    def get_course_splits(self, result: Result) -> List[Split]:
        if not result.person:
            return result.get_course_splits()
        course: Optional[Course] = self.find_course(result)
        if not course:
            return []
        return result.get_course_splits(course)

    def new_result(self, obj=None):
        if obj is None:
            obj = ResultSportident
        new_result = obj()
        new_result.days = self.get_days()
        return new_result

    def add_new_person(self, append_to_race=False):
        new_person = Person()
        if append_to_race:
            self.add_person(new_person)
        return new_person

    def add_person(self, new_person: Person):
        self.persons.insert(0, new_person)
        self.index_person(new_person)

    def index_person(self, person: Person):
        # update index
        if person.bib > 0:
            self.person_index_bib[person.bib] = person
        if person.card_number > 0:
            self.person_index_card[person.card_number] = person

    def add_new_group(self, append_to_race=False):
        new_group = Group()
        if append_to_race:
            self.groups.insert(0, new_group)
        return new_group

    def add_new_course(self, append_to_race=False):
        new_course = Course()
        if append_to_race:
            self.courses.insert(0, new_course)
        return new_course

    def add_new_organization(self, append_to_race=False):
        new_organization = Organization()
        if append_to_race:
            self.organizations.insert(0, new_organization)
        return new_organization

    def update_counters(self):
        # recalculate group counters
        for i in self.groups:
            i.count_person = 0
            i.count_finished = 0

        for i in self.organizations:
            i.count_person = 0
            i.count_finished = 0

        for i in self.persons:
            if i.group:
                i.group.count_person += 1
                if i.result_count > 0:
                    i.group.count_finished += 1
            if i.organization:
                i.organization.count_person += 1
                if i.result_count > 0:
                    i.organization.count_finished += 1

        # recalculate course counters
        for i in self.courses:
            i.count_person = 0
            i.count_finished = 0
            i.count_group = 0

        for i in self.groups:
            if i.course:
                i.course.count_person += i.count_person
                i.course.count_finished += i.count_finished
                i.course.count_group += 1

    def get_persons_by_group(self, group):
        return find(self.persons, group=group, return_all=True)

    def get_persons_by_corridor(self, corridor):
        ret = []
        for person in self.persons:
            if person.group and person.group.start_corridor == corridor:
                ret.append(person)
        return ret

    def add_new_result(self, result):
        ignore_punches_before_start = self.get_setting(
            "ignore_punches_before_start", False
        )
        if ignore_punches_before_start:
            start = result.get_start_time()
            finish = result.get_finish_time()

            if finish < start and start.hour < 22 and finish != OTime(0):
                logging.info(
                    f"Ignoring finish with time before start: {finish} for card {result.card_number}"
                )
                return

        self.results.insert(0, result)

    def add_result(self, result):
        for r in self.results:
            if r is result:
                break
        else:
            self.add_new_result(result)

    def clear_results(self):
        for result in self.results:
            result.clear()

    def is_relay(self):
        if self.data.race_type == RaceType.RELAY:
            return True
        return False

    def get_lengths(self):
        return (
            len(self.persons),
            len(self.results),
            len(self.groups),
            len(self.courses),
            len(self.organizations),
        )

    def get_duplicate_card_numbers(self):
        ret = []
        current_card = -1
        previous_person = None
        for person in sorted(self.persons, key=lambda x: x.card_number):
            if person.card_number > 0 and person.card_number == current_card:
                if previous_person:
                    ret.append(previous_person)
                    previous_person = None
                ret.append(person)
            else:
                previous_person = person
                current_card = person.card_number
        return ret

    def get_duplicate_names(self):
        ret = []
        current_name = ""
        previous_person = None
        for person in sorted(self.persons, key=lambda x: x.full_name):
            if person.full_name and person.full_name == current_name:
                if previous_person:
                    ret.append(previous_person)
                    previous_person = None
                ret.append(person)
            else:
                previous_person = person
                current_name = person.full_name
        return ret

    def find_result_by_person_id(self, person_id) -> Optional[Result]:
        if len(self.result_index) < 1:
            for res in self.results:
                if res.person:
                    id = res.person.multi_day_id
                    self.result_index[id] = res

        if person_id in self.result_index:
            return self.result_index[person_id]
        else:
            return None


class Qualification(IntEnum):
    NOT_QUALIFIED = 0
    I_Y = 1
    II_Y = 2
    III_Y = 3
    I = 4  # noqa
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
            "": 0,
            " ": 0,
            "б/р": 0,
            "IIIю": 3,
            "IIю": 2,
            "Iю": 1,
            "III": 6,
            "II": 5,
            "I": 4,
            "КМС": 7,
            "МС": 8,
            "МСМК": 9,
            "ЗМС": 9,
        }
        if name not in qual_reverse:
            return cls(0)

        return cls(qual_reverse[name])

    def get_title(self):
        qual = {
            "": "б/р",
            0: "б/р",
            3: "IIIю",
            2: "IIю",
            1: "Iю",
            6: "III",
            5: "II",
            4: "I",
            7: "КМС",
            8: "МС",
            9: "МСМК",
        }
        return qual[self.value]

    # get score for ranking, stored in config.ini file
    def get_score(self):
        ret = Config().ranking.get(self.name.lower(), 0)
        ret = float(ret)
        return ret

    @staticmethod
    def list_qual():
        return [q.get_title() for q in Qualification]


class RankingItem:
    def __init__(
        self,
        qual=Qualification.NOT_QUALIFIED,
        use_scores=True,
        max_place=0,
        max_time=None,
        is_active=True,
    ):
        self.qual = qual
        self.use_scores = use_scores
        self.max_place = max_place
        self.max_time = max_time
        self.is_active = is_active
        self.percent = 0
        self.min_scores = 0

    def get_dict_data(self):
        ret = {}
        ret["qual"] = self.qual.get_title()
        ret["max_place"] = self.max_place
        ret["max_time"] = str(self.max_time)
        ret["min_scores"] = str(self.min_scores) if self.min_scores else None
        ret["percent"] = self.percent
        return ret

    def to_dict(self):
        ret = {}
        ret["qual"] = self.qual.value
        ret["use_scores"] = self.use_scores
        ret["max_place"] = str(self.max_place)
        ret["max_time"] = self.max_time.to_msec() if self.max_time else None
        ret["min_scores"] = str(self.min_scores) if self.min_scores else None
        ret["is_active"] = self.is_active
        ret["percent"] = self.percent
        return ret

    def update_data(self, data):
        self.qual = Qualification.get_qual_by_code(int(data["qual"]))
        self.use_scores = bool(data["use_scores"])
        self.max_place = int(data["max_place"])
        if data["max_time"]:
            self.max_time = OTime(msec=int(data["max_time"]))
        if "min_scores" in data and data["min_scores"]:
            self.min_scores = data["min_scores"]
        self.is_active = bool(data["is_active"])
        self.percent = int(data["percent"])


class Ranking:
    def __init__(self):
        self.is_active = False
        self.rank_scores = 0
        self.rank = {}
        self.rank[Qualification.MS] = RankingItem(
            qual=Qualification.MS, use_scores=False, max_place=2, is_active=False
        )
        self.rank[Qualification.KMS] = RankingItem(
            qual=Qualification.KMS, use_scores=False, max_place=6, is_active=False
        )
        self.rank[Qualification.I] = RankingItem(qual=Qualification.I)
        self.rank[Qualification.II] = RankingItem(qual=Qualification.II)
        self.rank[Qualification.III] = RankingItem(qual=Qualification.III)
        self.rank[Qualification.I_Y] = RankingItem(qual=Qualification.I_Y)
        self.rank[Qualification.II_Y] = RankingItem(qual=Qualification.II_Y)
        self.rank[Qualification.III_Y] = RankingItem(qual=Qualification.III_Y)

    def get_max_qual(self):
        max_qual = Qualification.NOT_QUALIFIED
        for i in self.rank.values():
            if i.is_active:
                if i.max_place or (i.max_time and i.max_time.to_msec() > 0):
                    if max_qual.get_score() < i.qual.get_score():
                        max_qual = i.qual
        return max_qual

    def get_dict_data(self):
        ret = {}
        ret["is_active"] = self.is_active
        if self.is_active:
            ret["rank_scores"] = self.rank_scores
            ret["max_qual"] = self.get_max_qual().get_title()
            rank_array = []

            for i in self.rank.values():
                if i.is_active:
                    if i.max_place or (i.max_time and i.max_time.to_msec() > 0):
                        rank_array.append(i.get_dict_data())

            ret["rank"] = rank_array
        return ret

    def to_dict(self):
        ret = {}
        ret["is_active"] = self.is_active
        ret["rank_scores"] = self.rank_scores
        ret["rank"] = []
        for i in self.rank:
            obj = self.rank[i]
            rank = obj.to_dict()
            ret["rank"].append(rank)
        return ret

    def update_data(self, data):
        self.is_active = bool(data["is_active"])
        if "rank_scores" in data:
            self.rank_scores = int(data["rank_scores"])
        for i in data["rank"]:
            rank = RankingItem()
            rank.update_data(i)
            self.rank[rank.qual] = rank


class RelayLeg:
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
        self.variant = ""
        self.person: Person = None
        self.result: Result = None
        self.course = None  # optional link to the course, prefer to use variant and bib to find course
        self.team = team

    def __eq__(self, other) -> bool:
        return self.leg == other.leg

    def __gt__(self, other) -> bool:
        return self.leg > other.leg

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
                for cur_leg in team.legs:
                    if cur_leg.leg == self.leg - 1:
                        return cur_leg
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
        arr = str(text).split(":")
        if len(arr) == 2:
            bib_array = arr[0].split(".")
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
            return res.is_status_ok()
        return True

    def is_out_of_competition(self):
        res = self.get_result()
        if res and res.person:
            return res.person.is_out_of_competition
        return False

    def set_bib(self):
        if self.person:
            self.person.set_bib(self.get_bib())

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
            return res.get_finish_time()
        return None

    def get_start_time(self):
        res = self.get_result()
        if res:
            return res.get_start_time()
        return None

    def set_start_time_from_previous(self):
        if self.leg > 1:
            prev_leg = self.get_prev_leg()
            if prev_leg:
                if prev_leg.is_finished():
                    self.set_start_time(prev_leg.get_finish_time())
                    return 1
        return 0

    def set_place(self, place):
        res = self.get_result()
        if res and isinstance(res, Result):
            res.place = place

    def set_order(self, order):
        res = self.get_result()
        if res and isinstance(res, Result):
            res.order = order


class RelayTeam:
    def __init__(self, r):
        self.race = r
        self.group: Group = None
        self.legs: List[RelayLeg] = []
        self.description = ""  # Name of team, optional
        self.bib_number = None  # bib
        self.last_finished_leg = 0
        self.last_correct_leg = 0
        self.place = 0
        self.order = 0

    def __eq__(self, other) -> bool:
        if self.get_is_status_ok() == other.get_is_status_ok():
            if self.get_correct_lap_count() == other.get_correct_lap_count():
                if self.get_time() == other.get_time():
                    return True
        return False

    def __gt__(self, other) -> bool:
        """ "Greater" means worse, ranks lower on the result list"""

        if self.get_is_status_ok() and not other.get_is_status_ok():
            return False

        if not self.get_is_status_ok() and other.get_is_status_ok():
            return True

        if self.get_correct_lap_count() != other.get_correct_lap_count():
            return self.get_correct_lap_count() < other.get_correct_lap_count()

        if not self.get_is_out_of_competition() and other.get_is_out_of_competition():
            return False

        if self.get_is_out_of_competition() and not other.get_is_out_of_competition():
            return True

        return self.get_time() > other.get_time()

    def get_all_results(self):
        """return: all results of persons, connected with team"""

    def add_result(self, result):
        """Add new result to the team"""
        leg = RelayLeg(self)
        leg.set_result(result)
        leg.set_person(result.person)
        leg.leg = result.person.bib // 1000

        # Reset relay team name if athletes are from different organizations
        if result.person and result.person.organization:
            if self.description != result.person.organization.name:
                self.description = ""

        self.legs.append(leg)

    def set_leg_for_person(self, person, leg):
        """Set leg for person"""

    def set_bibs(self, number):
        """Set bibs for all members, e.g. 1001, 2001, 3001 for 1,2,3 legs of team #1"""

    def set_start_times(self):
        """Set start time as finish of previous leg for all members"""
        for i in self.legs:
            i.set_start_time_from_previous()

    def get_leg(self, leg_number):
        for i in self.legs:
            if i.leg == leg_number:
                return i
        return None

    def get_time(self):
        if len(self.legs):
            last_correct_leg = self.get_correct_lap_count()
            if last_correct_leg > 0:
                last_finish = self.get_leg(last_correct_leg).get_finish_time()
                start = self.get_leg(1).get_start_time()
                time = last_finish - start
                for i in range(last_correct_leg):
                    time += self.get_leg(i + 1).result.get_penalty_time()
                    time -= self.get_leg(i + 1).result.get_credit_time()
                return time

        return OTime()

    def get_lap_finished(self):
        """quantity of already finished laps"""
        finished_qty = 0
        for leg in self.legs:
            if leg.is_finished():
                finished_qty += 1
        return finished_qty

    def get_correct_lap_count(self):
        """quantity of successfully finished laps"""
        correct_qty = 0
        for i in range(len(self.legs)):
            leg = self.get_leg(i + 1)
            if not leg:
                return correct_qty
            if leg.is_correct():
                correct_qty += 1
            else:
                return correct_qty
        return correct_qty

    def get_is_team_placed(self):
        """Is the team taking place? - the team has completed all stages,
        the status is ok and there are no participants out of competition
        """
        return (
            self.get_is_status_ok()
            and self.get_is_all_legs_finished()
            and not self.get_is_out_of_competition()
        )

    def get_is_status_ok(self):
        """Get the whole team status - OK if all laps are OK"""
        for leg in self.legs:
            if not leg.is_correct():
                return False
        return True

    def get_is_all_legs_finished(self):
        # check leg count
        leg_count = race().data.relay_leg_count
        return len(self.legs) >= leg_count

    def get_is_out_of_competition(self):
        """Get the whole team status - True if any lap is out of competition"""
        for leg in self.legs:
            if leg.is_out_of_competition():
                return True
        if self.group and self.group.is_best_team_placing_mode:
            if not self.description:
                return True
        return False

    def set_place(self, place):
        self.place = place
        for i in self.legs:
            i.set_place(place)

    def set_order(self, order):
        self.order = order
        for i in self.legs:
            i.set_order(order)


def create(obj, **kwargs):
    return obj.create(**kwargs)


def update(obj, **kwargs):
    obj.update(**kwargs)


def find(iterable: list, **kwargs):
    if len(kwargs.items()) == 0:
        return None
    return_all = kwargs.pop("return_all", False)
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
current_race = 0


def new_event(event):
    if len(event):
        global _event
        _event = event


def add_race():
    _event.append(create(Race))


def copy_race():
    cur_race = race()
    copy = Race()
    obj = cur_race.to_dict()
    obj["id"] = str(copy.id)
    copy.update_data(obj)
    _event.append(copy)


def move_up_race():
    index = get_current_race_index()
    if index > 0:
        tmp = _event[index]
        _event[index] = _event[index - 1]
        _event[index - 1] = tmp
        set_current_race_index(index - 1)


def move_down_race():
    index = get_current_race_index()
    if index < len(_event) - 1:
        tmp = _event[index]
        _event[index] = _event[index + 1]
        _event[index + 1] = tmp
        set_current_race_index(index + 1)


def del_race():
    # Leave at least 1 race
    if len(_event) > 1:
        index = get_current_race_index()
        _event.remove(_event[index])
        if index > 0:
            set_current_race_index(index - 1)


def set_current_race_index(index):
    if len(_event) > index:
        global current_race
        current_race = index


def get_current_race_index():
    return current_race


def races():
    return _event


def race(i=None):
    if i is None:
        i = get_current_race_index()
    else:
        i = 0

    if i < len(_event):
        return _event[i]
    else:
        return Race()
