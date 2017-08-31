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
    # ret = datetime(1970, 1, 1) + timedelta(seconds= value/100, milliseconds=value*10%1000)
    # ret = datetime.datetime.fromtimestamp(int(value)/100.0)
    # TODO Find more simple solution!!!
    # ret = datetime.time(value // 360000, (value % 360000) // 6000, (value % 6000) // 100, (value % 100) * 10000)
    today = datetime.datetime.now()
    assert (isinstance(today, datetime.datetime))
    ret = datetime.datetime(today.year, today.month, today.day, value // 360000 % 24, (value % 360000) // 6000,
                            (value % 6000) // 100, (value % 100) * 10000)

    return ret
