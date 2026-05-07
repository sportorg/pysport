#[pyo3::pymodule]
mod sportorg_rust_example {
    use pyo3::prelude::*;

    #[pyfunction]
    fn status_message() -> &'static str {
        "Rust works"
    }
}
