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
uv sync --frozen
uv sync --frozen --extra win  # for Windows
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
