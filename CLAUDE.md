# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync --frozen              # base
uv sync --frozen --extra win  # Windows (adds pywin32, pyImpinj)

# Run application (also regenerates translations)
uv run poe run

# Development cycle
uv run poe format        # Ruff format
uv run poe lint          # Ruff check + dead-fixture checks
uv run poe test          # pytest with coverage (42% branch threshold)
uv run poe test-fast     # pytest --exitfirst (iterate quickly)
uv run poe test-failed   # pytest --last-failed
uv run poe all           # format + lint + test

# Translations (required after editing .po files)
uv run poe generate-mo

# Build Windows executable
python builder.py build
```

To run a single test: `uv run pytest tests/test_<name>.py -vv`

## Architecture

**SportOrg** is a PySide6 desktop application for managing orienteering competitions. Entry point: `SportOrg.pyw` → `sportorg/gui/main.py` (`Application` singleton) → `sportorg/gui/main_window.py` (`MainWindow`).

### Layer overview

| Layer | Location | Role |
|-------|----------|------|
| GUI | `sportorg/gui/` | Main window, tabbed views (persons/results/groups/courses/organizations), dialogs |
| Models | `sportorg/models/memory.py` | Core domain objects: `Race`, `Person`, `Result`, `Group`, `Course`, `Organization` |
| Constants | `sportorg/models/constant.py` | Enumerations: result status, system types, countries, qualifications |
| Modules | `sportorg/modules/` | Feature plugins: hardware readers, live results, printing, backup, teamwork |
| Libs | `sportorg/libs/` | Format parsers: IOF XML, OCAD, WinOrient WDB |
| Common | `sportorg/common/` | Shared utilities: `otime.py` (time math), `singleton.py`, `template.py` |

### Hardware integrations (under `sportorg/modules/`)

`sportident/`, `sfr/`, `sportiduino/`, `rfid_impinj/`, `srpid/` — each provides a reader client attached to `MainWindow`. Mock hardware adapters in tests; never hit physical devices.

### Key files

- `sportorg/models/memory.py` — all core domain models; understand this first
- `sportorg/modules/backup/json.py` — race serialization/deserialization
- `sportorg/config.py` — path constants, logging, debug mode
- `sportorg/language.py` — i18n; `.po` source files in `languages/<locale>/LC_MESSAGES/`, compiled to `.mo` at runtime

## Coding Conventions

- **Python 3.8** is the production target (Windows compatibility); avoid syntax/APIs unavailable in 3.8
- Type hints required on all functions (mypy strict mode — `disallow_untyped_defs = true`)
- PascalCase for GUI classes, snake_case for functions, UPPER_SNAKE_CASE for constants
- Ruff defaults for formatting (4-space indent); run `uv run poe format` before committing

## Commits

Conventional Commits format: `<type>(<scope>): <summary>` (summary: present tense, no cap, no period, ≤70 chars).

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

Example: `feat(live): add Orgeo client`

## Configuration & Secrets

Sensitive values (live endpoints, Telegram tokens) go in local config files under `configs/` — never committed. Use `aiohttp` mocks in tests to prevent accidental external traffic.
