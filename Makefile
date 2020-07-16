BIN ?= .venv/bin/

CODE = sportrog
ALL_CODE = sportrog tests

.PHONY: run
run:
	$(BIN)python SportOrg.pyw

.PHONY: venv
venv:
	python -m venv .venv
	$(BIN)pip install poetry
	$(BIN)poetry install

.PHONY: update
update:
	$(BIN)poetry update

.PHONY: test
test:
	$(BIN)pytest --verbosity=2 --showlocals --strict --log-level=DEBUG $(args)

.PHONY: lint
lint:
	$(BIN)flake8 --jobs 4 --statistics --show-source $(ALL_CODE)
	$(BIN)pylint --jobs 1 --rcfile=setup.cfg $(CODE)
	$(BIN)black --skip-string-normalization --line-length=88 --check $(ALL_CODE)
	$(BIN)pytest --dead-fixtures --dup-fixtures
	$(BIN)mypy $(ALL_CODE)
	$(BIN)mkdocs build -s

.PHONY: format
format:
	$(BIN)autoflake --recursive --in-place --remove-all-unused-imports $(ALL_CODE)
	$(BIN)isort --apply --recursive $(ALL_CODE)
	$(BIN)black --skip-string-normalization --line-length=88 $(ALL_CODE)
	$(BIN)unify --in-place --recursive $(ALL_CODE)
