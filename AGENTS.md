# Repository Guidelines

## Project Structure & Module Organization
`sportorg/` holds the core application: GUI elements live under `sportorg/gui`, hardware/data integrations under `sportorg/modules`, and shared utilities in `sportorg/common` and `sportorg/utils`. PySide resources and other assets reside in `img/`, `sounds/`, `templates/`, and `styles/`. Configuration defaults are under `configs/`, while CLI helpers sit at the repo root (`SportOrg.pyw`, `builder.py`). Tests are colocated in `tests/`, with sample fixtures in `tests/data/`. Languages files live in `languages/<locale>/LC_MESSAGES/` and must be regenerated via the `generate-mo` task after edits.

## Build, Test, and Development Commands
- `uv sync --frozen [--extra win]`: install locked dependencies for Python 3.8 environments.
- `uv run poe run`: regenerate translations and launch the GUI (`SportOrg.pyw`) in debug mode.
- `uv run poe format` / `uv run poe lint`: run Ruff formatting, Ruff linting, and fixture sanity checks.
- `uv run poe test`, `uv run poe test-fast`, `uv run poe test-failed`: execute the pytest suites with coverage, fail-fast, or rerun modes.
- `python builder.py build`: create the cx_Freeze desktop bundle (Windows friendly).

## Coding Style & Naming Conventions
Python files use 4-space indentation, type hints where practical, and follow Ruff’s defaults (`ruff format` for layout, `ruff check` for lint). Keep GUI classes PascalCase, helper functions snake_case, and configuration constants UPPER_SNAKE_CASE. Templates and translation IDs should mirror the GUI object names for easier traceability. Regenerate `.mo` files via `uv run poe generate-mo` after editing `.po` resources.

## Testing Guidelines
Pytest is the canonical framework; test files follow `tests/test_*` naming and should load fixtures from `tests/data/`. Add regression tests alongside affected modules (e.g., `tests/test_live.py` for `sportorg/modules/live`). Coverage thresholds are enforced at 42% branch coverage, so include `--cov` results locally before opening a PR. Prefer `uv run poe test-fast` while iterating and `uv run poe test` before committing. Mock hardware adapters (SportIdent, RFID, SRPID) instead of hitting physical devices.

## Commit & Pull Request Guidelines
Use Conventional Commits (`feat(live): add Orgeo client`) and keep summaries under 70 characters. Each PR should include: purpose, behavioural changes, test evidence (`uv run poe test` output), and any screenshots impacting the GUI (store captures under `img/` if they belong in docs). Link related issues in the description and request reviews from domain owners (`modules/<area>` maintainers). Keep PRs focused; split large changes into feature and cleanup branches rather than mixing refactors with functional work.

## Security & Configuration Tips
Sensitive credentials (e.g., live result endpoints, Telegram tokens) must be provided via local config files and never committed—use entries in `configs/` as templates and add real values to `.gitignored` overrides. When testing network modules, stub responses with `aiohttp` mocks to prevent accidental external traffic. Always confirm Windows-specific behaviour under Python 3.8 because production bundles target that interpreter.
