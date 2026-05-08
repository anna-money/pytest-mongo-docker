.PHONY: all uv deps lint test black isort flake8 mypy build

UV_EXTRA_ARGS ?=

all: deps lint test

uv:
	@which uv >/dev/null 2>&1 || { echo "uv is not installed"; exit 1; }

deps: uv
	@uv sync --all-extras

black: deps
	@uv run $(UV_EXTRA_ARGS) black --line-length 120 pytest_mg tests

isort: deps
	@uv run $(UV_EXTRA_ARGS) isort --line-length 120 --use-parentheses --multi-line 3 --combine-as --trailing-comma pytest_mg tests

flake8: deps
	@uv run $(UV_EXTRA_ARGS) flake8 --max-line-length 120 --ignore C901,C812,E203,E704 --extend-ignore W503 pytest_mg tests

mypy: deps
	@uv run $(UV_EXTRA_ARGS) mypy --strict --ignore-missing-imports pytest_mg tests

lint: black isort flake8 mypy

test: deps
	@uv run $(UV_EXTRA_ARGS) pytest -vv --rootdir tests .

build: uv
	@uv build
