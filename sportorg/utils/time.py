try:
    from PySide6.QtCore import QDate, QTime
except ModuleNotFoundError:
    from PySide2.QtCore import QDate, QTime

from datetime import date, datetime, timedelta
from sportorg.common.otime import OTime


def time_to_otime(t) -> OTime:
    if isinstance(t, datetime):
        return OTime(0, t.hour, t.minute, t.second, round(t.microsecond / 1000))
    if isinstance(t, QTime):
        return OTime(0, t.hour(), t.minute(), t.second(), t.msec())
    if isinstance(t, timedelta):
        return time_to_otime(datetime(2000, 1, 1, 0, 0, 0) + t)
    if isinstance(t, OTime):
        return t
    return OTime()


def time_iof_to_otime(t) -> OTime:
    str_t = str(t)
    if str_t.find("T") > 0:
        time_part = str_t[str_t.find("T") + 1 :]
        if time_part.find("+") > 0:
            time_part = time_part[: time_part.find("+")]
        return hhmmss_to_time(time_part)
    return OTime()


def time_to_datetime(t) -> datetime:
    otime = time_to_otime(t)
    return datetime(2000, 1, 1, otime.hour, otime.minute, otime.sec, otime.msec * 1000)


def time_to_qtime(t) -> OTime:
    otime = time_to_otime(t)
    time_ = QTime()
    time_.setHMS(otime.hour, otime.minute, otime.sec, otime.msec)
    return time_


def _int_to_time(value) -> datetime:
    """convert value from 1/100 s to time"""

    today = datetime.now()
    ret = datetime(
        today.year,
        today.month,
        today.day,
        value // 360000 % 24,
        (value % 360000) // 6000,
        (value % 6000) // 100,
        (value % 100) * 10,
    )
    return ret


def int_to_otime(value) -> OTime:
    """convert value from 1/100 s to otime"""
    ret = OTime(
        0,
        value // 360000 % 24,
        (value % 360000) // 6000,
        (value % 6000) // 100,
        (value % 100) * 10,
    )
    return ret


def time_to_int(value):
    """convert value from time to 1/100s"""
    return round(time_to_sec(value) * 100)


def time_to_mmss(value):
    time_ = time_to_datetime(value)
    return str(time_.strftime("%M:%S"))


def time_to_hhmmss(value):
    time_ = time_to_datetime(value)
    return time_.strftime("%H:%M:%S")


def date_to_yyyymmdd(value):
    return value.strftime("%Y.%m.%d")


def date_to_ddmmyyyy(value):
    return value.strftime("%d.%m.%Y")


def ddmmyyyy_to_time(value):
    try:
        return datetime.strptime(value, "%d.%m.%Y")
    except (ValueError, TypeError):
        return datetime(1900, 1, 1)


def hhmmss_to_time(value):
    arr = str(value).split(":")
    if len(arr) == 3:
        msec = 0
        secs = arr[2].split(".")
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
    return time_to_mmss(time_km) + "/km"


def qdate_to_date(value):
    return date(year=value.year(), month=value.month(), day=value.day())


def date_to_qdate(value):
    return QDate(value.year, value.month, value.day)


def str_to_date(value, separator="-"):
    day, month, year = str(value).split(separator)
    return date(int(year), int(month), int(day))


def yyyymmdd_to_date(value, separator="-"):
    year, month, day = str(value).split(separator)
    return date(int(year), int(month), int(day))
