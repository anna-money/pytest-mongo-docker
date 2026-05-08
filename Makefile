.PHONY: all uv deps lint test ruff ruff-fix format mypy build

UV_EXTRA_ARGS ?=

all: deps lint test

uv:
	@which uv >/dev/null 2>&1 || { echo "uv is not installed"; exit 1; }

deps: uv
	@uv sync --all-extras

ruff: deps
	@uv run ruff check pytest_mg tests
	@uv run ruff format --check pytest_mg tests

ruff-fix: deps
	@uv run ruff check --fix pytest_mg tests
	@uv run ruff format pytest_mg tests

format: ruff-fix

mypy: deps
	@uv run $(UV_EXTRA_ARGS) mypy --strict --ignore-missing-imports pytest_mg tests

lint: ruff mypy

test: deps
	@uv run $(UV_EXTRA_ARGS) pytest -vv --rootdir tests .

build: uv
	@uv build
