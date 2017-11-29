import datetime


class OTime:
    def __init__(self, day=0, hour=0, minute=0, sec=0, msec=0):
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
        if not other:
            return False
        return self.to_msec() == other.to_msec()

    def __gt__(self, other):
        if not other:
            return True
        return self.to_msec() > other.to_msec()

    def __ge__(self, other):
        return self.to_msec() >= other.to_msec()

    def __add__(self, other):
        return OTime(msec=(self.to_msec() + other.to_msec()))

    def __sub__(self, other):
        return OTime(msec=(self.to_msec() - other.to_msec()))

    def __int__(self):
        return self.to_msec()

    def __str__(self):
        return '{}:{}:{}'.format(
            self.hour + self.day*24,
            self.minute if self.minute > 9 else '0' + str(self.minute),
            self.sec if self.sec > 9 else '0' + str(self.sec)
        )

    def __repr__(self):
        return self.__str__()

    def __truediv__(self, fl):
        return OTime(msec=(int(self.to_msec() / fl)))

    @classmethod
    def now(cls):
        now = datetime.datetime.now()
        return OTime(0, now.hour, now.minute, now.second, round(now.microsecond / 1000))

    def replace(self, day=None, hour=None, minute=None, sec=None, msec=None):
        return OTime(
            self.if_none(day, self.day),
            self.if_none(hour, self.hour),
            self.if_none(minute, self.minute),
            self.if_none(sec, self.sec),
            self.if_none(msec, self.msec)
        )

    def copy(self):
        return OTime(msec=self.to_msec())

    def to_sec(self, n=0):
        return round(self.to_msec()/1000, n)

    def to_msec(self):
        return self._msec

    def to_time(self):
        return datetime.time(self.hour, self.minute, self.sec, self.msec*1000)

    @staticmethod
    def get_msec(day=0, hour=0, minute=0, sec=0, msec=0):
        return day*86400000 + hour*3600000 + minute*60000 + sec*1000 + msec

    @staticmethod
    def if_none(val, default=None):
        return default if val is None else val


def otime(hour=0, minute=0, sec=0, msec=0):
    return OTime(0, hour, minute, sec, msec)
