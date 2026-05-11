## v0.0.9 (2026-05-08)

* No runtime changes. Test suite expanded with mocked unit tests for `is_mongo_ready` driver selection, `find_unused_local_port`, `_ensure_image`, and `run_mongo` / `run_mongo_replicaset` cleanup and error paths
* Added `pytester`-based test verifying `pytest11` entry-point registration (catches packaging regressions)
* Standalone `mongo` fixture now pings the container; replica-set smoke broadened to `mongo_rs` (latest) in addition to `mongo_6_rs`
* Added `pytest-cov` dev dep and local `make coverage` target (no CI job, no threshold enforced)
* CI: scope `setup-uv` cache per matrix cell (`cache-suffix`) to avoid `setup-uv-2-…` cache-reservation race warnings across parallel Python/pytest jobs
* Refactor tests: split `test_utils.py` by SUT into `test_resolve_docker_host.py`, `test_find_unused_local_port.py`, `test_is_mongo_ready.py`; rename `test_fixtures_unit.py` → `test_fixtures.py`; drop duplicated `test_utils_more.py` and `test_is_mongo_ready_selection.py`; consolidate ping helper in `test_mongo.py`
* Remove `motor` branch from `is_mongo_ready` selection chain. `motor` hard-depends on `pymongo`, so the pymongo factory always wins first — the motor branch was unreachable. Chain is now `pymongo > dummy`; drop the now-private `_try_get_is_mongo_ready_based_on_motor` helper and its tests
* Replace pymongo-based `is_mongo_ready` ping with a raw `socket.create_connection` probe. Drops the driver-selection chain (`_try_get_is_mongo_ready_based_on_pymongo`, `_get_dummy_is_mongo_ready`, `IsReadyFunc` protocol). `run_mongo_replicaset` now reuses the same readiness helper instead of an inline socket loop
* Extract container lifecycle into private `_start_mongo_container` context manager. `run_mongo` and `run_mongo_replicaset` now share Docker client setup, image pull, port allocation, container creation/start, readiness poll, and teardown; the RS path adds only `replSetInitiate` + primary-election wait on top. Teardown is now best-effort for both fixtures — kill/remove errors during cleanup never fail tests
* Split `pytest_mg.fixtures` into `pytest_mg.runners` (container lifecycle: `Mongo`, `run_mongo`, `run_mongo_replicaset`) and `pytest_mg.fixtures` (pytest fixture wrappers only). Public API (`pytest_mg.Mongo`, `pytest_mg.run_mongo`, `pytest_mg.run_mongo_replicaset`) is unchanged
* `make coverage`: switch from `pytest --cov` to `coverage run -m pytest` so coverage starts before the `pytest11` plugin loads. Reported coverage rises from ~57% to ~95% — the previous number was a measurement artifact; module-level imports and `def` lines were running before pytest-cov activated
* Parametrize integration smoke tests over `mongo` and `mongo_*_rs` fixtures, so the previously-untested `mongo_5_rs`, `mongo_7_rs`, and `mongo_8_rs` wrappers are now exercised. Coverage reaches 99%
* `is_mongo_ready`: after a successful socket probe, optionally verify the server is serving wire commands via `pymongo.admin.command("ping")` (with `directConnection=True` so it works on uninitiated replica-set nodes). Falls back to socket-only when pymongo is not installed

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
