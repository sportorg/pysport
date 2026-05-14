use pyo3::prelude::*;
use pyo3::types::PyModule;

use crate::otime::OTime;

mod otime;

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
