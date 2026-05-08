.PHONY: all uv deps lint test mypy pre-commit pre-commit-install pre-commit-update build

UV_EXTRA_ARGS ?=

all: deps lint test

uv:
	@which uv >/dev/null 2>&1 || { echo "uv is not installed"; exit 1; }

deps: uv
	@uv sync --all-extras

mypy: deps
	@uv run $(UV_EXTRA_ARGS) mypy --strict --ignore-missing-imports pytest_mg tests

pre-commit-install: deps
	@uv run pre-commit install

pre-commit: deps
	@uv run pre-commit run --all-files

pre-commit-update: deps
	@uv run pre-commit autoupdate

lint: pre-commit mypy

test: deps
	@uv run $(UV_EXTRA_ARGS) pytest -vv --rootdir tests .

build: uv
	@uv build
