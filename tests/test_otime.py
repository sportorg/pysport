import pytest

from sportorg.common.otime import OTime, PythonOTime, TimeRounding, parse_time_rounding


OTIME_IMPLEMENTATIONS = (
    (PythonOTime,) if OTime is PythonOTime else (PythonOTime, OTime)
)


@pytest.fixture(params=OTIME_IMPLEMENTATIONS, ids=lambda cls: cls.__name__)
def otime_cls(request):
    return request.param


@pytest.mark.parametrize(
    ("time1", "time2", "expected"),
    [
        ((1, 13, 5, 35), (1, 13, 5, 35), "37:05:35"),
        ((1, 13, 15, 35), (1, 13, 15, 35), "37:15:35"),
        ((2, 26, 5, 35), (3, 2, 5, 35), "74:05:35"),
        ((0, 26, 5, 35), (1, 2, 5, 35), "26:05:35"),
        ((0, 0, 5, 35), (0, 0, 5, 35), "00:05:35"),
        ((0, 185, 0, 0), (7, 17, 0, 0), "185:00:00"),
    ],
)
def test_otime(otime_cls, time1, time2, expected):
    time = otime_cls(*time1)
    assert time2[0] == time.day
    assert time2[1] == time.hour
    assert time2[2] == time.minute
    assert time2[3] == time.sec
    assert expected == str(time)


def test_otime_eq(otime_cls):
    otime1 = otime_cls(0, 0, 25, 44)
    otime2 = otime_cls(0, 0, 25, 44)
    otime3 = otime_cls(0, 0, 26, 44)

    # TODO: real day difference, now we have limitation of 24h for race and add 1 day to negative value
    assert otime2 - otime3 > otime_cls()

    assert otime3 - otime2 > otime_cls()
    assert otime1 == otime2
    assert otime1 <= otime2
    assert otime1 <= otime3
    assert otime3 >= otime2
    assert not otime1 > otime3
    assert otime1 < otime3
    assert otime1 != otime3
    assert otime1 == otime2


def test_otime_sum(otime_cls):
    otime1 = otime_cls(0, 0, 25, 40)
    otime2 = otime_cls(0, 0, 25, 20)
    otime3 = otime_cls(0, 0, 51, 0)
    otime4 = otime_cls(0, 0, 0, 20)
    assert otime1 + otime2 == otime3
    assert otime1 + otime2 == otime3
    assert otime1 - otime2 == otime4


@pytest.mark.parametrize(
    ("time_rounding", "expected"),
    [
        (TimeRounding.math, 1200),
        (TimeRounding.down, 1200),
        (TimeRounding.up, 1300),
    ],
)
def test_otime_round_accepts_int(otime_cls, time_rounding, expected):
    assert otime_cls(msec=1250).round(1, time_rounding).to_msec() == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("math", TimeRounding.math),
        ("down", TimeRounding.down),
        ("up", TimeRounding.up),
    ],
)
def test_parse_time_rounding(value, expected):
    assert parse_time_rounding(value) == expected


def test_parse_time_rounding_invalid():
    with pytest.raises(ValueError, match="time_rounding is invalid"):
        parse_time_rounding("unknown")
