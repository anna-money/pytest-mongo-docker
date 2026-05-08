# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

pytest-mongo-docker is a pytest plugin that provides session-scoped MongoDB fixtures backed by Docker containers. It automatically pulls images, allocates ports, mounts data to tmpfs for speed, and cleans up containers after tests.

## Commands

Toolchain: `uv` (deps + build + publish). Build backend: `hatchling` + `hatch-vcs` (version derived from git tags).

```bash
make deps          # uv sync --all-extras (installs project + dev deps)
make lint          # Run all linters (black, isort, flake8, mypy)
make test          # Run tests
make all           # deps + lint + test
make build         # uv build (sdist + wheel)

# Run a single test
uv run pytest -vv --rootdir tests -k test_mongo_5

# Individual linters
make black         # Format code (line-length 120)
make isort         # Sort imports
make flake8        # Style checks
make mypy          # Strict type checking
```

Release: push a `v*` git tag. CI runs `uv build` + `uv publish` (token in `PYPI_TOKEN` secret). Version comes from the tag automatically — no source bump needed.

## Architecture

The plugin registers via the `pytest11` entry point in `pyproject.toml`, making fixtures automatically available when installed.

**Key files:**
- `pytest_mongo_docker/fixtures.py` — `Mongo` dataclass (host/port) and `run_mongo()` context manager that handles the full Docker container lifecycle (pull → create → start → readiness check → yield → kill → remove). All fixtures (`mongo`, `mongo_5`–`mongo_8`) are session-scoped and delegate to `run_mongo()` with different image tags.
- `pytest_mongo_docker/utils.py` — Port allocation and MongoDB readiness detection. Readiness checking uses a fallback chain: pymongo → motor → dummy (always ready). Neither pymongo nor motor is a hard dependency.
- `tests/conftest.py` — Loads the plugin via `pytest_plugins = ["pytest_mongo_docker"]`. With `uv sync` the project is installed editable, so the entry point is also live.

## Style

- Line length: 120
- Type annotations required everywhere (`mypy --strict`)
- Formatting: black + isort

## CI

GitHub Actions matrix tests across Python 3.9–3.13 and pytest 7.4.x–8.3.x. Deploys to PyPI on git tags.