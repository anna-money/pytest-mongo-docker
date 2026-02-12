# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

pytest-mongo is a pytest plugin that provides session-scoped MongoDB fixtures backed by Docker containers. It automatically pulls images, allocates ports, mounts data to tmpfs for speed, and cleans up containers after tests.

## Commands

```bash
make deps          # Install/upgrade all dependencies
make lint          # Run all linters (black, isort, flake8, mypy)
make test          # Run tests
make all           # deps + lint + test

# Run a single test
python3 -m pytest -vv --rootdir tests -k test_mongo_5

# Individual linters
make black         # Format code (line-length 120)
make isort         # Sort imports
make flake8        # Style checks
make mypy          # Strict type checking
```

## Architecture

The plugin registers via the `pytest11` entry point in setup.py, making fixtures automatically available when installed.

**Key files:**
- `pytest_mongo/fixtures.py` — `Mongo` dataclass (host/port) and `run_mongo()` context manager that handles the full Docker container lifecycle (pull → create → start → readiness check → yield → kill → remove). All fixtures (`mongo`, `mongo_5`–`mongo_8`) are session-scoped and delegate to `run_mongo()` with different image tags.
- `pytest_mongo/utils.py` — Port allocation and MongoDB readiness detection. Readiness checking uses a fallback chain: pymongo → motor → dummy (always ready). Neither pymongo nor motor is a hard dependency.
- `tests/conftest.py` — Loads the plugin via `pytest_plugins = ["pytest_mongo"]` (needed because the plugin isn't pip-installed during development).

## Style

- Line length: 120
- Type annotations required everywhere (`mypy --strict`)
- Formatting: black + isort

## CI

GitHub Actions matrix tests across Python 3.9–3.13 and pytest 7.4.x–8.3.x. Deploys to PyPI on git tags.