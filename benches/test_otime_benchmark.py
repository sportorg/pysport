import pytest

from sportorg.common.otime import OTime, PythonOTime, TimeRounding


OTIME_IMPLEMENTATIONS = (PythonOTime,) if OTime is PythonOTime else (PythonOTime, OTime)


def _exercise_otime(cls):
    base = cls(0, 1, 2, 3, 401)
    total = 0
    for index in range(250):
        value = cls(
            day=index % 3,
            hour=index % 27,
            minute=index % 60,
            sec=index % 60,
            msec=index % 1000,
        )
        _ = value == value
        _ = value > base
        _ = value >= base
        total += value.to_msec(2)
        total += value.to_sec()
        total += value.to_minute()
        total += len(value.to_str(3))
        total += int(((value + base) - base).round(1, TimeRounding.down))
        total += int(((value + base) - base).round(1, TimeRounding.up))
        total += int(((value + base) - base).round(1, TimeRounding.math))
        total += int((value * 1.5) / 2)
    return total


@pytest.mark.parametrize(
    "otime_cls", OTIME_IMPLEMENTATIONS, ids=lambda cls: cls.__name__
)
def test_otime_operations(benchmark, otime_cls):
    expected = _exercise_otime(PythonOTime)
    result = benchmark(_exercise_otime, otime_cls)
    assert result == expected
