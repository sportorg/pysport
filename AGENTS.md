# Repository Guidelines

## Project Structure & Module Organization
- Core application code is in `sportorg/`.
- GUI elements are in `sportorg/gui`.
- Hardware and data integrations are in `sportorg/modules`.
- Shared utilities are in `sportorg/common` and `sportorg/utils`.
- PySide resources and assets are in `img/`, `sounds/`, `templates/`, and `styles/`.
- Configuration defaults are in `configs/`.
- CLI helpers are at the repository root: `SportOrg.pyw`, `builder.py`.
- Tests are in `tests/`, with sample fixtures in `tests/data/`.
- Translation files are in `languages/<locale>/LC_MESSAGES/`.
- After editing `.po` files, regenerate `.mo` files via `generate-mo`.

## Build, Test, and Development Commands
- `uv sync --frozen [--extra win]`: install locked dependencies for Python 3.8 environments.
- `uv run poe run`: regenerate translations and launch `SportOrg.pyw` in debug mode.
- `uv run poe format`: run Ruff formatting.
- `uv run poe lint`: run Ruff linting and fixture sanity checks.
- `uv run poe test`: run full pytest suite with coverage.
- `uv run poe test-fast`: run fail-fast test mode.
- `uv run poe test-failed`: rerun failed tests.
- `python builder.py build`: create a cx_Freeze desktop bundle (Windows-friendly).

## Coding Style & Naming Conventions
- Use 4-space indentation in Python files.
- Use type hints where practical.
- Follow Ruff defaults: `ruff format` for formatting and `ruff check` for linting.
- Use PascalCase for GUI classes.
- Use snake_case for helper functions.
- Use UPPER_SNAKE_CASE for configuration constants.
- Keep templates and translation IDs aligned with GUI object names.
- Regenerate `.mo` files after editing `.po` resources via `uv run poe generate-mo`.
- Write all code comments in English.

## Python Compatibility
- Keep all code compatible with Python 3.8 and the latest stable Python release (currently Python 3.14).
- Use language features and standard-library APIs that are available in Python 3.8.
- If newer features are required, add explicit version-conditional branches.
- Ensure version-conditional branches provide equivalent fallback implementations.

## Testing Guidelines
- Use pytest as the primary testing framework.
- Name test files as `tests/test_*`.
- Load fixtures from `tests/data/`.
- Add regression tests near affected modules, for example `tests/test_live.py` for `sportorg/modules/live`.
- Maintain at least 42% branch coverage.
- Check local `--cov` results before opening a PR.
- Use `uv run poe test-fast` during iteration.
- Run `uv run poe test` before committing.
- Mock hardware adapters (SportIdent, RFID, SRPID) instead of using physical devices.

## Commit & Pull Request Guidelines
- Use Conventional Commits, for example `feat(live): add Orgeo client`.
- Keep commit summaries under 70 characters.
- Include PR purpose.
- Include behavioral changes.
- Include test evidence, such as `uv run poe test` output.
- Include GUI screenshots when relevant.
- Store documentation screenshots under `img/` when appropriate.
- Link related issues in the PR description.
- Request reviews from relevant domain owners, such as `modules/<area>` maintainers.
- Keep PRs focused.
- Split large work into feature and cleanup branches instead of mixing refactors with functional changes.

## Security & Configuration Tips
- Keep sensitive credentials (for example live result endpoints and Telegram tokens) in local config files only.
- Never commit secrets.
- Use `configs/` entries as templates.
- Put real secret values in `.gitignored` overrides.
- Stub network-module responses with `aiohttp` mocks during tests.
- Avoid accidental external traffic in tests.
- Verify Windows-specific behavior under Python 3.8 because production bundles target that interpreter.
