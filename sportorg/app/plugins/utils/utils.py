import datetime
from datetime import timedelta

from PyQt5.QtCore import QTime

print('utils plugin')


def qtime2datetime(t):
    now = datetime.datetime.now()
    assert isinstance(t, QTime)
    new_time = datetime.datetime(now.year, now.month, now.day, t.hour(), t.minute(), t.second(), t.msec())
    return new_time


def datetime2qtime(t):
    assert isinstance(t, datetime.datetime)
    time = QTime()
    time.setHMS(t.hour, t.minute, t.second, t.microsecond)
    return time


def timedelta2datetime(t):
    assert isinstance(t, datetime.timedelta)
    now = datetime.datetime.now()
    new_time = datetime.datetime(now.year, now.month, now.day, 0, 0, 0)
    new_time += t
    return new_time


def int_to_time(value):
    """ convert value from 1/100 s to time """

    today = datetime.datetime.now()
    assert (isinstance(today, datetime.datetime))
    ret = datetime.datetime(today.year, today.month, today.day, value // 360000 % 24, (value % 360000) // 6000,
                            (value % 6000) // 100, (value % 100) * 10000)
    return ret


def time_to_int(value):
    """ convert value from time to 1/100s """
    return round(time_to_sec(value) * 100)


def time_to_hhmmss(value):
    if isinstance(value, datetime.datetime):
        return str(value.strftime("%H:%M:%S"))
    if isinstance(value, QTime):
        return time_to_hhmmss(qtime2datetime(value))
    if isinstance(value, datetime.timedelta):
        return time_to_hhmmss(timedelta2datetime(value))
    return value


def time_to_mmss(value):
    if isinstance(value, datetime.datetime):
        return str(value.strftime("%M:%S"))
    if isinstance(value, QTime):
        return time_to_mmss(qtime2datetime(value))
    if isinstance(value, datetime.timedelta):
        return time_to_mmss(timedelta2datetime(value))
    return value


def time_remove_day(value):
    assert isinstance(value, datetime.datetime)
    new_value = datetime.datetime(year=2000, month=1, day=1, hour=value.hour, minute=value.minute,
                                  second=value.second, microsecond=value.microsecond)
    return new_value


def time_to_sec(value, max_val=86400):  # default max value = 24h
    if isinstance(value, datetime.datetime):
        ret = value.hour * 3600 + value.minute * 60 + value.second + value.microsecond / 1000000
        if max_val:
            ret = ret % max_val
        return ret

    if isinstance(value, QTime):
        return time_to_sec(qtime2datetime(value), max_val)

    return 0


def time_to_minutes(value, max_val=24*60):
    return time_to_sec(value, max_val*60) / 60


def get_speed_min_per_km(time, length_m):
    time_km = time / (length_m / 1000)
    return time_to_mmss(time_km) + "/km"
