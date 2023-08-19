# Contributing

## Get Started

```
python3.8 -m venv .venv
```

```
pip install poetry
poetry install
poetry install -E win  # for Windows
```

Add `DEBUG=True` to `.env` file or `cp .env.example .env`

```
poetry run python SportOrg.pyw
```

## Build

### cx_Freeze

`python builder.py build`
