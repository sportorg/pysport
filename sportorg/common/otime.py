import datetime
from enum import Enum
from math import trunc
from typing import Optional


class TimeRounding(Enum):
    math = 0
    down = 1
    up = 2


class OTime:
    def __init__(
        self, day: int = 0, hour: int = 0, minute: int = 0, sec: int = 0, msec: int = 0
    ):
        self._msec = self.get_msec(day, hour, minute, sec, msec)
        self._args = None

    @property
    def day(self):
        return self.args[0]

    @property
    def hour(self):
        return self.args[1]

    @property
    def minute(self):
        return self.args[2]

    @property
    def sec(self):
        return self.args[3]

    @property
    def msec(self):
        return self.args[4]

    @property
    def args(self):
        if self._args is None:
            day = self._msec // 86400000
            hour = (self._msec % 86400000) // 3600000
            minute = ((self._msec % 86400000) % 3600000) // 60000
            sec = (((self._msec % 86400000) % 3600000) % 60000) // 1000
            msec = (((self._msec % 86400000) % 3600000) % 60000) % 1000

            self._args = day, hour, minute, sec, msec

        return self._args

    def __eq__(self, other):
        if not isinstance(other, OTime):
            return False
        return self.to_msec() == other.to_msec()

    def __gt__(self, other):
        if not isinstance(other, OTime):
            return True
        return self.to_msec() > other.to_msec()

    def __ge__(self, other):
        if not isinstance(other, OTime):
            return False
        return self.to_msec() >= other.to_msec()

    def __add__(self, other):
        return OTime(msec=(self.to_msec() + other.to_msec()))

    def __sub__(self, other):
        return OTime(msec=(self.to_msec() - other.to_msec()))

    def __mul__(self, mlt):
        return OTime(msec=int(self.to_msec() * mlt))

    def __truediv__(self, div):
        return OTime(msec=int(self.to_msec() / div))

    def __int__(self):
        return self.to_msec()

    def __str__(self):
        return self.to_str()

    def __repr__(self):
        return self.__str__()

    def __bool__(self):
        return self.to_msec() != 0

    @classmethod
    def now(cls) -> "OTime":
        now = datetime.datetime.now()
        return OTime(0, now.hour, now.minute, now.second, round(now.microsecond / 1000))

    def replace(self, day=None, hour=None, minute=None, sec=None, msec=None) -> "OTime":
        return OTime(
            self.if_none(day, self.day),
            self.if_none(hour, self.hour),
            self.if_none(minute, self.minute),
            self.if_none(sec, self.sec),
            self.if_none(msec, self.msec),
        )

    def copy(self) -> "OTime":
        return OTime(msec=self.to_msec())

    def to_minute(self):
        return trunc(self.to_msec() / (1000 * 60))

    def to_sec(self):
        return trunc(self.to_msec() / 1000)

    def to_msec(self, sub_sec: int = 3) -> int:
        if not 0 <= sub_sec <= 3:
            sub_sec = 3
        mlt = 10 ** (3 - sub_sec)
        return self._msec // mlt * mlt

    def to_time(self):
        return datetime.time(self.hour, self.minute, self.sec, self.msec * 1000)

    def to_minute_str(self):
        minute = int(self.to_msec() / (1000 * 60))
        return "{}:{}".format(
            minute if minute > 9 else "0" + str(minute),
            self.sec if self.sec > 9 else "0" + str(self.sec),
        )

    @staticmethod
    def get_msec(day=0, hour=0, minute=0, sec=0, msec=0):
        ret = day * 86400000 + hour * 3600000 + minute * 60000 + sec * 1000 + msec
        if ret < 0:
            # emulation of midnight - add 1 day if time < 0.
            # Note, that now we don't support races > 24h
            # TODO: real day difference, support races > 24h
            ret += 86400000
        return ret

    @staticmethod
    def if_none(val: Optional[int], default: int) -> int:
        return default if val is None else val

    def to_str(self, time_accuracy: int = 0) -> str:
        hour = self.hour + self.day * 24
        if time_accuracy == 0:
            return f"{hour:02}:{self.minute:02}:{self.sec:02}"
        elif time_accuracy == 3:
            return f"{hour:02}:{self.minute:02}:{self.sec:02}.{self.msec:003}"
        elif time_accuracy == 2:
            return f"{hour:02}:{self.minute:02}:{self.sec:02}.{self.msec // 10:02}"
        elif time_accuracy == 1:
            return f"{hour:02}:{self.minute:02}:{self.sec:02}.{self.msec // 100}"
        raise ValueError("time_accuracy is invalid")

    def round(
        self, time_accuracy: int = 0, time_rounding: TimeRounding = TimeRounding.math
    ) -> "OTime":
        ms = self.to_msec()
        multiplier = 10 ** (3 - time_accuracy)
        if time_rounding == TimeRounding.math:
            new_ms = int(round(ms / multiplier)) * multiplier
        elif time_rounding == TimeRounding.down:
            new_ms = ms // multiplier * multiplier
        else:
            new_ms = -(-ms // multiplier) * multiplier  # math.ceil is slower

        return OTime(msec=new_ms)
