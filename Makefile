CODE = sportorg tests

.PHONY: run
run:
	poetry run python SportOrg.pyw

.PHONY: update
update:
	poetry update

.PHONY: test
test:
	pytest --verbosity=2 --showlocals --strict --log-level=DEBUG $(args) --cov

.PHONY: lint
lint:
	# flake8 --jobs 4 --statistics --show-source $(CODE)
	# pylint --jobs 1 --rcfile=setup.cfg $(CODE)
	black --skip-string-normalization --line-length=88 --check $(CODE)
	pytest --dead-fixtures --dup-fixtures
	mypy $(CODE)

.PHONY: format
format:
	autoflake --recursive --in-place --remove-all-unused-imports $(CODE)
	isort $(CODE)
	black --skip-string-normalization --line-length=88 $(CODE)
	unify --in-place --recursive $(CODE)
