# Contributing

## Get Started

### Preparation

SportOrg runs on Python 3.8 for compatibility with Windows 7. Latest Python 3.8 release with binary installers is [Python 3.8.10](https://www.python.org/downloads/release/python-3810/).

During development, the [uv](https://docs.astral.sh/uv/) and [poe](https://poethepoet.natn.io/) tools are used. The preferred method for installing these utilities is [pipx](https://pipx.pypa.io/).

It may be necessary to restart the terminal window during the installation process to update the `PATH` environment variable.

```
pip install pipx
pipx ensurepath
pipx install uv
```

### Create Virtual Environment

Get pysport project.

```
git clone https://github.com/sportorg/pysport.git
cd pysport
```

If multiple versions of Python are installed, it is necessary to specify the path to the Python 3.8 executable file.

```
uv python install 3.8
```

Install requirements.

```
uv sync --frozen --extra gui
uv sync --frozen --extra win --extra gui  # for Windows
```

### Run SportOrg

```
uv run poe run
```

## Write a code

```
uv run poe format
uv run poe lint
uv run poe test
```

## Build

### cx_Freeze

`python builder.py build`

### Windows 7

Windows 7 needs an environment of its own. The build follows whichever Qt
binding is installed, so no separate builder command exists — prepare the
environment, then build as usual.

Three dependencies must be held back. Anything built with Rust 1.78 or newer
links `WaitOnAddress` / `WakeByAddressAll` from `api-ms-win-core-synch-l1-2-0.dll`
statically instead of resolving them at run time; Windows 7 does not export
them, so the module fails to load with "the specified procedure could not be
found":

| Dependency   | Last version that runs on Windows 7 | First broken version |
|--------------|-------------------------------------|----------------------|
| orjson       | `3.10.13`                           | `3.10.14`            |
| cryptography | `42.0.8`                            | `43.0.3`             |
| Qt           | `PySide2` (Qt5)                     | any `PySide6` (Qt6)  |

`cryptography` 43 and newer additionally call `ProcessPrng`, which is Windows 10
only. Qt6 needs Windows 10 as well, so Qt5 is the last usable toolkit.

Pin them in `pyproject.toml` before syncing:

```toml
gui = [
  "PySide2>=5.15,<6",
]
```

```toml
  "cryptography>=41,<=42.0.8",
  "orjson>=3.9.5,<=3.10.13",
```

Then build:

```
uv sync --all-extras --python 3.8
uv run poe generate-mo
uv run poe generate-version
uv run python builder.py build
```

Package the result as a portable archive:

```powershell
$version = (uv run python -c "from sportorg.config import VERSION; print(VERSION)").Trim()
$buildDir = (Get-ChildItem build -Directory -Filter 'exe.*' | Select-Object -First 1).FullName
New-Item -ItemType Directory -Force dist | Out-Null
Compress-Archive -Path "$buildDir\*" -DestinationPath "dist\sportorg-$version-win7-64.zip" -Force
```

`uv run python builder.py bdist_msi` also works and produces an installer.

Do not commit the pins: the released artifacts are built against PySide6 and
current dependencies, and these ceilings would silently downgrade them.

## Commit Message Format

This project adheres to [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).
A specification for adding human and machine readable meaning to commit messages.

### Commit Message Header

```
<type>(<scope>): <short summary>
  │       │             │
  │       │             └─⫸ Summary in present tense. Not capitalized. No period at the end.
  │       │
  │       └─⫸ Commit Scope
  │
  └─⫸ Commit Type: feat|fix|build|ci|docs|perf|refactor|test|chore
```

#### Type

| type     | name                     | description                                                                                            |
|----------|--------------------------|--------------------------------------------------------------------------------------------------------|
| feat     | Features                 | A new feature                                                                                          |
| fix      | Bug Fixes                | A bug fix                                                                                              |
| docs     | Documentation            | Documentation only changes                                                                             |
| style    | Styles                   | Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc) |
| refactor | Code Refactoring         | A code change that neither fixes a bug nor adds a feature                                              |
| perf     | Performance Improvements | A code change that improves performance                                                                |
| test     | Tests                    | Adding missing tests or correcting existing tests                                                      |
| build    | Builds                   | Changes that affect the build system or external dependencies (example scopes: mypy, pip, pytest)      |
| ci       | Continuous Integrations  | Changes to our CI configuration files and scripts (example scopes: Github Actions)                     |
| chore    | Chores                   | Other changes that don't modify src or test files                                                      |
| revert   | Reverts                  | Reverts a previous commit                                                                              |
