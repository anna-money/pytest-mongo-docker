## v0.0.8 (2026-05-08)

* Skip `docker pull` when image already present locally (inspect first, pull only on `ImageNotFound`)
* Tighten readiness polling intervals (500ms → 100ms) for standalone and replica set startup
* Lower pymongo/motor `serverSelectionTimeoutMS` (1000 → 300) so poll attempts fail fast during mongod boot
* Run mongod with explicit `--bind_ip_all --quiet` (RS keeps `--replSet`) to reduce startup log overhead
* Fix LICENSE copyright holder

## v0.0.7 (2026-05-08)

* Renamed project to `pytest-mg` (module `pytest_mg`, entry point updated)
* Migrated build to `uv` + `hatchling` + `hatch-vcs` with version derived from git tags (fixes source/tag drift that broke v0.0.6 PyPI upload)
* Switched lint/format to `ruff` (dropped black/isort/flake8 and pre-commit)
* Split publish into its own workflow using PyPI Trusted Publishing (OIDC, no token)
* Bumped min Python to 3.10, min pytest to 8.0; added Python 3.14 and pytest 9 to CI matrix
* Expanded pytest matrix to every minor (8.0.x–8.4.x, 9.0.x) plus latest-of-major rolling pins
* Switched license metadata to PEP 639 SPDX expression; added Topic/Typing classifiers and PyPI keywords
* Bumped dev deps: mypy 2.0.0, pymongo 4.17.0, pytest 9.0.3
* CODEOWNERS handover to `@anna-money/backend`

## v0.0.6 (2026-04-29)

* Resolve `DOCKER_HOST` from active `docker context` so non-default setups (Colima, custom contexts) work without manually exporting the variable; no-op when `DOCKER_HOST` is already set or the docker CLI is missing

## v0.0.5 (2026-03-04)

* Added replica set fixtures (`mongo_rs`, `mongo_5_rs`–`mongo_8_rs`) for change stream support
* Added pymongo as a dev dependency for readiness checking and replica set initialisation

## v0.0.1 (2026-02-11)

* A first version
