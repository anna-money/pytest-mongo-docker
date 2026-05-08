## Unreleased

* Skip `docker pull` when image already present locally (inspect first, pull only on `ImageNotFound`)
* Tighten readiness polling intervals (500ms → 100ms) for standalone and replica set startup
* Lower pymongo/motor `serverSelectionTimeoutMS` (1000 → 300) so poll attempts fail fast during mongod boot
* Run mongod with explicit `--bind_ip_all --quiet` (RS keeps `--replSet`) to reduce startup log overhead

## v0.0.5 (2026-03-04)

* Added replica set fixtures (`mongo_rs`, `mongo_5_rs`–`mongo_8_rs`) for change stream support
* Added pymongo as a dev dependency for readiness checking and replica set initialisation

## v0.0.1 (2026-02-11)

* A first version
