# pytest-mongo-docker

A pytest plugin that provides session-scoped MongoDB fixtures backed by Docker containers.

## Features

- **Zero configuration** — Fixtures work out of the box, no setup required
- **Automatic lifecycle management** — Pulls images, allocates ports, starts containers, and cleans up after tests
- **Fast** — Data directory mounted to tmpfs for maximum speed
- **Version-specific fixtures** — Test against MongoDB 5, 6, 7, 8, or latest
- **Replica set fixtures** — Drop-in variants with `--replSet` enabled for change stream support
- **Session-scoped** — One container per test session, shared across all tests

## Installation

```bash
pip install pytest-mongo-docker
```

## Requirements

- Python 3.9+
- pytest 7.4+
- docker 7.0+
- Docker daemon running locally or accessible via `DOCKER_HOST` environment variable

## Usage

### Basic Example

The plugin automatically registers fixtures when installed. Import the `Mongo` type for type hints:

```python
import pymongo
import pytest_mongo_docker


def test_pymongo(mongo: pytest_mongo_docker.Mongo):
    client = pymongo.MongoClient(host=mongo.host, port=mongo.port)

    db = client["test_db"]
    collection = db["test_collection"]

    collection.insert_one({"key": "value"})
    doc = collection.find_one({"key": "value"})

    assert doc["key"] == "value"

    client.close()
```

### Available Fixtures

All fixtures are session-scoped and return a `Mongo` object with `host` and `port` attributes:

**Standalone (default):**

- `mongo` — Latest MongoDB version (`mongo:latest`)
- `mongo_5` — MongoDB 5.x (`mongo:5`)
- `mongo_6` — MongoDB 6.x (`mongo:6`)
- `mongo_7` — MongoDB 7.x (`mongo:7`)
- `mongo_8` — MongoDB 8.x (`mongo:8`)

**Replica set** (required for change streams and transactions):

- `mongo_rs` — Latest MongoDB version (`mongo:latest`)
- `mongo_5_rs` — MongoDB 5.x (`mongo:5`)
- `mongo_6_rs` — MongoDB 6.x (`mongo:6`)
- `mongo_7_rs` — MongoDB 7.x (`mongo:7`)
- `mongo_8_rs` — MongoDB 8.x (`mongo:8`)

Replica set fixtures require `pymongo` (`pip install pymongo`) and start MongoDB with `--replSet rs0`. When connecting, use `directConnection=True` to avoid topology-discovery issues from the Docker port mapping:

```python
client = pymongo.MongoClient(
    f"mongodb://{mongo_6_rs.host}:{mongo_6_rs.port}/",
    directConnection=True,
)
```

### Advanced Example: Configuring Environment Variables

Use session-scoped `autouse` fixtures to configure your application before tests run:

```python
import os
import pytest
import pytest_mongo_docker


@pytest.fixture(scope="session", autouse=True)
def init_env(mongo_6: pytest_mongo_docker.Mongo) -> None:
    os.environ["MONGODB_CONNECTION_STRING"] = f"{mongo_6.host}:{mongo_6.port}"
    os.environ["MONGODB_DBNAME"] = "myapp"


def test_app():
    # Your application reads from environment variables,
    # no need to reference the fixture directly
    pass
```

### Using with Motor (async)

```python
import motor.motor_asyncio
import pytest
import pytest_mongo_docker


@pytest.mark.asyncio
async def test_motor(mongo: pytest_mongo_docker.Mongo):
    client = motor.motor_asyncio.AsyncIOMotorClient(host=mongo.host, port=mongo.port)

    db = client["test_db"]
    collection = db["test_collection"]

    await collection.insert_one({"key": "value"})
    doc = await collection.find_one({"key": "value"})

    assert doc["key"] == "value"

    client.close()
```

## How It Works

The plugin uses Docker's Python API to:
1. Pull the specified MongoDB image (if not already cached)
2. Allocate an unused local port
3. Create a container with data directory mounted to tmpfs
4. Start the container and wait for MongoDB to be ready
5. Yield the `Mongo` object with connection details
6. Kill and remove the container after all tests complete