from typing import Any

import pymongo
import pytest

import pytest_mongo_docker


def _ping(mongo: pytest_mongo_docker.Mongo) -> None:
    client: pymongo.MongoClient[Any] = pymongo.MongoClient(f"mongodb://{mongo.host}:{mongo.port}/")
    try:
        response = client.admin.command("ping")
        assert response["ok"] == 1.0
    finally:
        client.close()


def _assert_replicaset_functional(mongo: pytest_mongo_docker.Mongo) -> None:
    # Verify the replica set is functional by opening a change stream,
    # which requires a replica set and fails on standalone MongoDB.
    client: pymongo.MongoClient[Any] = pymongo.MongoClient(
        f"mongodb://{mongo.host}:{mongo.port}/",
        directConnection=True,
    )
    try:
        db = client["test_change_stream"]
        collection = db["events"]
        with collection.watch():
            pass
    finally:
        client.close()


@pytest.mark.parametrize("fixture_name", ["mongo", "mongo_5", "mongo_6", "mongo_7", "mongo_8"])
def test_mongo_standalone(request: pytest.FixtureRequest, fixture_name: str) -> None:
    mongo: pytest_mongo_docker.Mongo = request.getfixturevalue(fixture_name)
    _ping(mongo)


@pytest.mark.parametrize("fixture_name", ["mongo_rs", "mongo_5_rs", "mongo_6_rs", "mongo_7_rs", "mongo_8_rs"])
def test_mongo_replicaset(request: pytest.FixtureRequest, fixture_name: str) -> None:
    mongo: pytest_mongo_docker.Mongo = request.getfixturevalue(fixture_name)
    _assert_replicaset_functional(mongo)
