import pymongo
import pytest_mongo_docker


def test_mongo(mongo: pytest_mongo_docker.Mongo) -> None:
    assert mongo


def test_mongo_5(mongo_5: pytest_mongo_docker.Mongo) -> None:
    assert mongo_5


def test_mongo_6(mongo_6: pytest_mongo_docker.Mongo) -> None:
    assert mongo_6


def test_mongo_7(mongo_7: pytest_mongo_docker.Mongo) -> None:
    assert mongo_7


def test_mongo_8(mongo_8: pytest_mongo_docker.Mongo) -> None:
    assert mongo_8


def test_mongo_6_rs(mongo_6_rs: pytest_mongo_docker.Mongo) -> None:
    # Verify the replica set is functional by opening a change stream,
    # which requires a replica set and fails on standalone MongoDB.
    client = pymongo.MongoClient(
        f"mongodb://{mongo_6_rs.host}:{mongo_6_rs.port}/",
        directConnection=True,
    )
    try:
        db = client["test_change_stream"]
        collection = db["events"]
        with collection.watch():
            pass
    finally:
        client.close()