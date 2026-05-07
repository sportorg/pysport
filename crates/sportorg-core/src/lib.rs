use pyo3::basic::CompareOp;
use pyo3::exceptions::{PyValueError, PyZeroDivisionError};
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyModule, PyType};

const DAY_MSEC: i64 = 86_400_000;
const HOUR_MSEC: i64 = 3_600_000;
const MINUTE_MSEC: i64 = 60_000;
const SECOND_MSEC: i64 = 1_000;

#[pyclass(module = "sportorg_core", dict, skip_from_py_object)]
#[derive(Debug, Clone)]
struct OTime {
    msec: i64,
}

#[pymethods]
impl OTime {
    #[new]
    #[pyo3(signature = (day = 0, hour = 0, minute = 0, sec = 0, msec = 0))]
    fn new(day: i64, hour: i64, minute: i64, sec: i64, msec: i64) -> Self {
        Self {
            msec: Self::get_msec(day, hour, minute, sec, msec),
        }
    }

    #[getter]
    fn day(&self) -> i64 {
        self.args_tuple().0
    }

    #[getter]
    fn hour(&self) -> i64 {
        self.args_tuple().1
    }

    #[getter]
    fn minute(&self) -> i64 {
        self.args_tuple().2
    }

    #[getter]
    fn sec(&self) -> i64 {
        self.args_tuple().3
    }

    #[getter(msec)]
    fn sub_msec(&self) -> i64 {
        self.args_tuple().4
    }

    #[getter]
    fn args(&self) -> (i64, i64, i64, i64, i64) {
        self.args_tuple()
    }

    fn __richcmp__(&self, other: &Bound<'_, PyAny>, op: CompareOp) -> bool {
        let other_msec = other
            .extract::<PyRef<'_, OTime>>()
            .ok()
            .map(|obj| obj.msec)
            .or_else(|| other_to_msec(other).ok());

        match op {
            CompareOp::Eq => other_msec.map_or(false, |msec| self.msec == msec),
            CompareOp::Ne => other_msec.map_or(true, |msec| self.msec != msec),
            CompareOp::Gt => other_msec.map_or(true, |msec| self.msec > msec),
            CompareOp::Ge => other_msec.map_or(false, |msec| self.msec >= msec),
            CompareOp::Lt => other_msec.map_or(false, |msec| self.msec < msec),
            CompareOp::Le => other_msec.map_or(false, |msec| self.msec <= msec),
        }
    }

    fn __add__(&self, other: &Bound<'_, PyAny>) -> PyResult<Self> {
        Ok(Self::from_msec(self.msec + other_to_msec(other)?))
    }

    fn __sub__(&self, other: &Bound<'_, PyAny>) -> PyResult<Self> {
        Ok(Self::from_msec(self.msec - other_to_msec(other)?))
    }

    fn __mul__(&self, multiplier: f64) -> Self {
        Self::from_msec((self.msec as f64 * multiplier) as i64)
    }

    fn __truediv__(&self, divisor: f64) -> PyResult<Self> {
        if divisor == 0.0 {
            return Err(PyZeroDivisionError::new_err("division by zero"));
        }

        Ok(Self::from_msec((self.msec as f64 / divisor) as i64))
    }

    fn __int__(&self) -> i64 {
        self.to_msec(3)
    }

    fn __str__(&self) -> PyResult<String> {
        self.to_str(0)
    }

    fn __repr__(&self) -> PyResult<String> {
        self.__str__()
    }

    fn __bool__(&self) -> bool {
        self.to_msec(3) != 0
    }

    #[classmethod]
    fn now(cls: &Bound<'_, PyType>) -> PyResult<Self> {
        let py = cls.py();
        let datetime = PyModule::import(py, "datetime")?;
        let now = datetime.getattr("datetime")?.call_method0("now")?;
        let hour = now.getattr("hour")?.extract::<i64>()?;
        let minute = now.getattr("minute")?.extract::<i64>()?;
        let sec = now.getattr("second")?.extract::<i64>()?;
        let microsecond = now.getattr("microsecond")?.extract::<i64>()?;

        Ok(Self::new(
            0,
            hour,
            minute,
            sec,
            round_half_even_div(microsecond, SECOND_MSEC),
        ))
    }

    #[pyo3(signature = (day = None, hour = None, minute = None, sec = None, msec = None))]
    fn replace(
        &self,
        day: Option<i64>,
        hour: Option<i64>,
        minute: Option<i64>,
        sec: Option<i64>,
        msec: Option<i64>,
    ) -> Self {
        Self::new(
            day.unwrap_or_else(|| self.day()),
            hour.unwrap_or_else(|| self.hour()),
            minute.unwrap_or_else(|| self.minute()),
            sec.unwrap_or_else(|| self.sec()),
            msec.unwrap_or_else(|| self.sub_msec()),
        )
    }

    fn copy(&self) -> Self {
        Self::from_msec(self.to_msec(3))
    }

    fn to_minute(&self) -> i64 {
        self.to_msec(3) / MINUTE_MSEC
    }

    fn to_sec(&self) -> i64 {
        self.to_msec(3) / SECOND_MSEC
    }

    #[pyo3(signature = (sub_sec = 3))]
    fn to_msec(&self, sub_sec: i64) -> i64 {
        let sub_sec = if (0..=3).contains(&sub_sec) {
            sub_sec
        } else {
            3
        };
        let multiplier = 10_i64.pow((3 - sub_sec) as u32);

        self.msec.div_euclid(multiplier) * multiplier
    }

    fn to_time(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        let datetime = PyModule::import(py, "datetime")?;
        let time = datetime.getattr("time")?.call1((
            self.hour(),
            self.minute(),
            self.sec(),
            self.sub_msec() * SECOND_MSEC,
        ))?;

        Ok(time.unbind())
    }

    fn to_minute_str(&self) -> String {
        let minute = self.to_msec(3) / MINUTE_MSEC;
        format!("{}:{}", padded_2(minute), padded_2(self.sec()))
    }

    #[staticmethod]
    #[pyo3(signature = (day = 0, hour = 0, minute = 0, sec = 0, msec = 0))]
    fn get_msec(day: i64, hour: i64, minute: i64, sec: i64, msec: i64) -> i64 {
        let mut ret =
            day * DAY_MSEC + hour * HOUR_MSEC + minute * MINUTE_MSEC + sec * SECOND_MSEC + msec;
        if ret < 0 {
            ret += DAY_MSEC;
        }
        ret
    }

    #[staticmethod]
    fn if_none(val: Option<i64>, default: i64) -> i64 {
        val.unwrap_or(default)
    }

    #[pyo3(signature = (time_accuracy = 0))]
    fn to_str(&self, time_accuracy: i64) -> PyResult<String> {
        let hour = self.hour() + self.day() * 24;
        let value = match time_accuracy {
            0 => format!("{hour:02}:{:02}:{:02}", self.minute(), self.sec()),
            3 => format!(
                "{hour:02}:{:02}:{:02}.{:03}",
                self.minute(),
                self.sec(),
                self.sub_msec()
            ),
            2 => format!(
                "{hour:02}:{:02}:{:02}.{:02}",
                self.minute(),
                self.sec(),
                self.sub_msec() / 10
            ),
            1 => format!(
                "{hour:02}:{:02}:{:02}.{}",
                self.minute(),
                self.sec(),
                self.sub_msec() / 100
            ),
            _ => return Err(PyValueError::new_err("time_accuracy is invalid")),
        };

        Ok(value)
    }

    #[pyo3(signature = (time_accuracy = 0, time_rounding = 0))]
    fn round(&self, time_accuracy: i64, time_rounding: i64) -> PyResult<Self> {
        let multiplier = time_accuracy_multiplier(time_accuracy)?;
        let ms = self.to_msec(3);
        let new_ms = match time_rounding {
            0 => round_half_even_div(ms, multiplier) * multiplier,
            1 => ms.div_euclid(multiplier) * multiplier,
            _ => ceil_div(ms, multiplier) * multiplier,
        };

        Ok(Self::from_msec(new_ms))
    }
}

impl OTime {
    fn from_msec(msec: i64) -> Self {
        Self {
            msec: Self::get_msec(0, 0, 0, 0, msec),
        }
    }

    fn args_tuple(&self) -> (i64, i64, i64, i64, i64) {
        let day = self.msec.div_euclid(DAY_MSEC);
        let day_rem = self.msec.rem_euclid(DAY_MSEC);
        let hour = day_rem / HOUR_MSEC;
        let hour_rem = day_rem % HOUR_MSEC;
        let minute = hour_rem / MINUTE_MSEC;
        let minute_rem = hour_rem % MINUTE_MSEC;
        let sec = minute_rem / SECOND_MSEC;
        let msec = minute_rem % SECOND_MSEC;

        (day, hour, minute, sec, msec)
    }
}

#[pyfunction]
fn status() -> &'static str {
    "Ok"
}

#[pymodule]
fn sportorg_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<OTime>()?;
    m.add_function(wrap_pyfunction!(status, m)?)?;
    Ok(())
}

fn other_to_msec(other: &Bound<'_, PyAny>) -> PyResult<i64> {
    other.call_method0("to_msec")?.extract::<i64>()
}

fn time_accuracy_multiplier(time_accuracy: i64) -> PyResult<i64> {
    if !(0..=3).contains(&time_accuracy) {
        return Err(PyValueError::new_err("time_accuracy is invalid"));
    }

    Ok(10_i64.pow((3 - time_accuracy) as u32))
}

fn round_half_even_div(value: i64, divisor: i64) -> i64 {
    let quotient = value.div_euclid(divisor);
    let remainder = value.rem_euclid(divisor);
    let twice_remainder = remainder * 2;

    if twice_remainder < divisor {
        quotient
    } else if twice_remainder > divisor || quotient % 2 != 0 {
        quotient + 1
    } else {
        quotient
    }
}

fn ceil_div(value: i64, divisor: i64) -> i64 {
    let quotient = value.div_euclid(divisor);
    if value.rem_euclid(divisor) == 0 {
        quotient
    } else {
        quotient + 1
    }
}

fn padded_2(value: i64) -> String {
    if value > 9 {
        value.to_string()
    } else {
        format!("0{value}")
    }
}
