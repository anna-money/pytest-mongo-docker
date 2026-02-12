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
