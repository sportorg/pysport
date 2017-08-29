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