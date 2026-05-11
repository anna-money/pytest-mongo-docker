from collections.abc import Generator

import pytest

from .runners import Mongo, run_mongo, run_mongo_replicaset


@pytest.fixture(scope="session")
def mongo() -> Generator[Mongo, None, None]:
    with run_mongo("mongo:latest") as mongo:
        yield mongo


@pytest.fixture(scope="session")
def mongo_5() -> Generator[Mongo, None, None]:
    with run_mongo("mongo:5") as mongo:
        yield mongo


@pytest.fixture(scope="session")
def mongo_6() -> Generator[Mongo, None, None]:
    with run_mongo("mongo:6") as mongo:
        yield mongo


@pytest.fixture(scope="session")
def mongo_7() -> Generator[Mongo, None, None]:
    with run_mongo("mongo:7") as mongo:
        yield mongo


@pytest.fixture(scope="session")
def mongo_8() -> Generator[Mongo, None, None]:
    with run_mongo("mongo:8") as mongo:
        yield mongo


@pytest.fixture(scope="session")
def mongo_rs() -> Generator[Mongo, None, None]:
    with run_mongo_replicaset("mongo:latest") as mongo:
        yield mongo


@pytest.fixture(scope="session")
def mongo_5_rs() -> Generator[Mongo, None, None]:
    with run_mongo_replicaset("mongo:5") as mongo:
        yield mongo


@pytest.fixture(scope="session")
def mongo_6_rs() -> Generator[Mongo, None, None]:
    with run_mongo_replicaset("mongo:6") as mongo:
        yield mongo


@pytest.fixture(scope="session")
def mongo_7_rs() -> Generator[Mongo, None, None]:
    with run_mongo_replicaset("mongo:7") as mongo:
        yield mongo


@pytest.fixture(scope="session")
def mongo_8_rs() -> Generator[Mongo, None, None]:
    with run_mongo_replicaset("mongo:8") as mongo:
        yield mongo
