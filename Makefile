CODE = sportorg tests

.PHONY: run
run:
	python SportOrg.pyw

.PHONY: venv
venv:
	python -m venv .venv
	pip install poetry
	poetry install

.PHONY: update
update:
	poetry update

.PHONY: test
test:
	pytest --verbosity=2 --showlocals --strict --log-level=DEBUG $(args)

.PHONY: lint
lint:
	flake8 --jobs 4 --statistics --show-source $(CODE)
	pylint --jobs 1 --rcfile=setup.cfg $(CODE)
	black --skip-string-normalization --line-length=88 --check $(CODE)
	pytest --dead-fixtures --dup-fixtures
	mypy $(CODE)
	mkdocs build -s

.PHONY: format
format:
	# autoflake doesn`t remove multi line imports
	isort --apply --recursive --force-single-line-imports $(CODE)
	# Remove unused imports
	autoflake --recursive --in-place --remove-all-unused-imports $(CODE)
	isort --apply --recursive $(CODE)
	black --skip-string-normalization --line-length=88 $(CODE)
	unify --in-place --recursive $(CODE)
