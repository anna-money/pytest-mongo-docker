# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

pytest-mg is a pytest plugin that provides session-scoped MongoDB fixtures backed by Docker containers. It automatically pulls images, allocates ports, mounts data to tmpfs for speed, and cleans up containers after tests.

## Commands

Toolchain: `uv` (deps + build + publish). Build backend: `hatchling` + `hatch-vcs` (version derived from git tags).

```bash
make deps          # uv sync --all-extras (installs project + dev deps)
make lint          # Run ruff (check + format --check) and mypy
make test          # Run tests
make all           # deps + lint + test
make build         # uv build (sdist + wheel)

# Run a single test
uv run pytest -vv --rootdir tests -k test_mongo_5

# Individual targets
make ruff          # ruff check + ruff format --check
make ruff-fix      # ruff check --fix + ruff format (writes changes)
make format        # alias for ruff-fix
make mypy          # Strict type checking
```

Release: create a GitHub Release. The `Publish` workflow runs `uv build` and uploads via `pypa/gh-action-pypi-publish` using PyPI Trusted Publishing (OIDC, no token). Version comes from the underlying tag automatically — no source bump needed.

## Architecture

The plugin registers via the `pytest11` entry point in `pyproject.toml`, making fixtures automatically available when installed.

**Key files:**
- `pytest_mg/fixtures.py` — `Mongo` dataclass (host/port) and `run_mongo()` context manager that handles the full Docker container lifecycle (pull → create → start → readiness check → yield → kill → remove). All fixtures (`mongo`, `mongo_5`–`mongo_8`) are session-scoped and delegate to `run_mongo()` with different image tags.
- `pytest_mg/utils.py` — Port allocation and MongoDB readiness detection. Readiness checking uses a fallback chain: pymongo → motor → dummy (always ready). Neither pymongo nor motor is a hard dependency.
- `tests/conftest.py` — Loads the plugin via `pytest_plugins = ["pytest_mg"]`. With `uv sync` the project is installed editable, so the entry point is also live.

## Style

- Line length: 120
- Type annotations required everywhere (`mypy --strict`)
- Formatting + linting: `ruff` (`ruff check` + `ruff format`). Run `make ruff` to verify or `make ruff-fix` to auto-fix and reformat.

## CI

GitHub Actions matrix tests across Python 3.10–3.14 and pytest 8.0.x–9.0.x. Deploys to PyPI on git tags.
