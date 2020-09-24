import datetime
import time
from datetime import date

from PySide2.QtCore import QDate, QTime

from sportorg.common.otime import OTime


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            print('%r  %2.2f ms' % (method.__name__, (te - ts) * 1000))
        return result

    return timed


def time_to_otime(t):
    if isinstance(t, datetime.datetime):
        return OTime(0, t.hour, t.minute, t.second, round(t.microsecond / 1000))
    if isinstance(t, QTime):
        return OTime(0, t.hour(), t.minute(), t.second(), t.msec())
    if isinstance(t, datetime.timedelta):
        return time_to_otime(datetime.datetime(2000, 1, 1, 0, 0, 0) + t)
    if isinstance(t, OTime):
        return t
    return OTime()


def time_to_datetime(t):
    otime = time_to_otime(t)
    return datetime.datetime(
        2000, 1, 1, otime.hour, otime.minute, otime.sec, otime.msec * 1000
    )


def time_to_qtime(t):
    otime = time_to_otime(t)
    time_ = QTime()
    time_.setHMS(otime.hour, otime.minute, otime.sec, otime.msec)
    return time_


def _int_to_time(value):
    """ convert value from 1/100 s to time """

    today = datetime.datetime.now()
    ret = datetime.datetime(
        today.year,
        today.month,
        today.day,
        value // 360000 % 24,
        (value % 360000) // 6000,
        (value % 6000) // 100,
        (value % 100) * 10,
    )
    return ret


def int_to_otime(value):
    """ convert value from 1/100 s to otime """
    ret = OTime(
        0,
        value // 360000 % 24,
        (value % 360000) // 6000,
        (value % 6000) // 100,
        (value % 100) * 10,
    )
    return ret


def time_to_int(value):
    """ convert value from time to 1/100s """
    return round(time_to_sec(value) * 100)


def time_to_mmss(value):
    time_ = time_to_datetime(value)
    return str(time_.strftime('%M:%S'))


def time_to_hhmmss(value):
    time_ = time_to_datetime(value)
    return time_.strftime('%H:%M:%S')


def hhmmss_to_time(value):
    arr = str(value).split(':')
    if len(arr) == 3:
        msec = 0
        secs = arr[2].split('.')
        sec = int(secs[0])
        if len(secs) == 2:
            msec = int(secs[1])
            if len(secs[1]) == 1:
                msec *= 100
            elif len(secs[1]) == 2:
                msec *= 10
        return OTime(0, int(arr[0]), int(arr[1]), sec, msec)
    return OTime()


def time_remove_day(value):
    new_value = datetime.datetime(
        year=2000,
        month=1,
        day=1,
        hour=value.hour,
        minute=value.minute,
        second=value.second,
        microsecond=value.microsecond,
    )
    return new_value


def _time_to_sec(value, max_val=86400):  # default max value = 24h

    if isinstance(value, datetime.datetime):
        ret = (
            value.hour * 3600
            + value.minute * 60
            + value.second
            + value.microsecond / 1000000
        )
        if max_val:
            ret = ret % max_val
        return ret

    if isinstance(value, QTime):
        return time_to_sec(time_to_datetime(value), max_val)

    return 0


def time_to_sec(value, max_val=86400):  # default max value = 24h
    otime = time_to_otime(value)
    ret = otime.to_sec()

    if max_val:
        ret = ret % max_val
    return ret


def time_to_minutes(value, max_val=24 * 60):
    return time_to_sec(value, max_val * 60) / 60


def get_speed_min_per_km(time, length_m):
    time_km = time / (length_m / 1000)
    return time_to_mmss(time_km) + '/km'


def qdate_to_date(value):
    return date(year=value.year(), month=value.month(), day=value.day())


def date_to_qdate(value):
    return QDate(value.year, value.month, value.day)


def date_to_str(value, separator='-'):
    return '{:%m' + separator + '%d' + separator + '%Y}'.format(value)


def str_to_date(value, separator='-'):
    day, month, year = str(value).split(separator)
    return date(int(year), int(month), int(day))
