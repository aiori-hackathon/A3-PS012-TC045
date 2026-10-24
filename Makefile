.RECIPEPREFIX = >
.PHONY: help setup test clean
help:
> @echo "make setup  - create .venv and install dependencies"
> @echo "make test   - run unit tests"
> @echo "make clean  - remove caches"
setup:
> python3 -m venv .venv
> .venv/bin/pip install -e ".[dev]"
test:
> .venv/bin/python -m pytest -q
clean:
> rm -rf .pytest_cache build *.egg-info src/*.egg-info
