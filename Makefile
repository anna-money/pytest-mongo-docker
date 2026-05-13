.PHONY: all uv deps lint test ruff ruff-fix format mypy build coverage

UV_EXTRA_ARGS ?=

all: deps lint test

uv:
	@which uv >/dev/null 2>&1 || { echo "uv is not installed"; exit 1; }

deps: uv
	@uv sync --all-extras

ruff: deps
	@uv run ruff check pytest_mongo_docker tests
	@uv run ruff format --check pytest_mongo_docker tests

ruff-fix: deps
	@uv run ruff check --fix pytest_mongo_docker tests
	@uv run ruff format pytest_mongo_docker tests

format: ruff-fix

mypy: deps
	@uv run $(UV_EXTRA_ARGS) mypy --strict --ignore-missing-imports pytest_mongo_docker tests

lint: ruff mypy

test: deps
	@uv run $(UV_EXTRA_ARGS) pytest -vv --rootdir tests .

coverage: deps
	@uv run $(UV_EXTRA_ARGS) coverage erase
	@uv run $(UV_EXTRA_ARGS) coverage run -m pytest --rootdir tests .
	@uv run $(UV_EXTRA_ARGS) coverage report --show-missing
	@uv run $(UV_EXTRA_ARGS) coverage xml

build: uv
	@uv build
