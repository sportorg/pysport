CODE = sportorg tests

POETRY_RUN = poetry run

.PHONY: install-poetry
install-poetry:
	pip install poetry

.PHONY: install
install:
	poetry install

.PHONY: run
run:
	python SportOrg.pyw

.PHONY: test
test:
	$(POETRY_RUN) pytest --verbosity=2 --showlocals --strict --log-level=DEBUG $(args) --cov

.PHONY: lint
lint:
	# $(POETRY_RUN) flake8 --jobs 4 --statistics --show-source $(CODE)
	# $(POETRY_RUN) pylint --jobs 1 --rcfile=setup.cfg $(CODE)
	$(POETRY_RUN) black --skip-string-normalization --line-length=88 --check $(CODE)
	$(POETRY_RUN) pytest --dead-fixtures --dup-fixtures
	$(POETRY_RUN) mypy $(CODE)

.PHONY: format
format:
	$(POETRY_RUN) autoflake --recursive --in-place --remove-all-unused-imports $(CODE)
	$(POETRY_RUN) isort $(CODE)
	$(POETRY_RUN) black --skip-string-normalization --line-length=88 $(CODE)
	$(POETRY_RUN) unify --in-place --recursive $(CODE)

.PHONY: publish
publish:
	@poetry publish --build --no-interaction --username=$(pypi_username) --password=$(pypi_password)