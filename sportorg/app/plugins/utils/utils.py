import datetime

from PyQt5.QtCore import QTime

print('utils plugin')


def qtime2datetime(t):
    now = datetime.datetime.now()
    assert (isinstance(t, QTime))
    new_time = datetime.datetime(now.year, now.month, now.day, t.hour(), t.minute(), t.second(), t.msec())
    return new_time


def datetime2qtime(t):
    assert(isinstance(t, datetime.datetime))
    time = QTime()
    time.setHMS(t.hour, t.minute, t.second, t.microsecond)
    return time


def int_to_time(value):
    """ convert value from 1/100 s to time """

    today = datetime.datetime.now()
    assert (isinstance(today, datetime.datetime))
    ret = datetime.datetime(today.year, today.month, today.day, value // 360000 % 24, (value % 360000) // 6000,
                            (value % 6000) // 100, (value % 100) * 10000)
    return ret


def time_to_int(value):
    """ convert value from time to 1/100s """

    if value is None:
        return 0

    assert isinstance(value, datetime.datetime)
    ret = value.hour * 3600 * 100 + \
        value.minute * 60 * 100 + \
        value.second * 100 + \
        round(value.microsecond / 10000)
    return ret


def time_to_hhmmss(value):
    if isinstance(value, datetime.datetime):
        return value.strftime("%H:%M:%S")
    if isinstance(value, QTime):
        return time_to_hhmmss(qtime2datetime(value))
    return value

def time_remove_day(value):
    assert isinstance(value, datetime.datetime)
    new_value = datetime.datetime(year=2000, month=1, day=1, hour=value.hour, minute=value.minute,
                                  second=value.second, microsecond=value.microsecond)
    return new_value
