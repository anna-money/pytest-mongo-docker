import socket
import sys
import types
from unittest import mock

import pymongo.errors
import pytest

from pytest_mg.utils import (
    _get_dummy_is_mongo_ready,
    _try_get_is_mongo_ready_based_on_motor,
    _try_get_is_mongo_ready_based_on_pymongo,
    find_unused_local_port,
)


def test_find_unused_local_port_returns_int_in_user_range() -> None:
    port = find_unused_local_port()
    assert isinstance(port, int)
    assert 1024 <= port <= 65535


def test_find_unused_local_port_socket_is_released() -> None:
    port = find_unused_local_port()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
    finally:
        s.close()


def test_find_unused_local_port_returns_distinct_ports_across_calls() -> None:
    ports = {find_unused_local_port() for _ in range(5)}
    assert len(ports) > 1


def test_pymongo_is_mongo_ready_success() -> None:
    client = mock.MagicMock()
    client.admin.command.return_value = {"ok": 1.0}
    with mock.patch("pymongo.MongoClient", return_value=client):
        factory = _try_get_is_mongo_ready_based_on_pymongo()
        assert factory is not None
        assert factory(host="127.0.0.1", port=27017) is True
    client.admin.command.assert_called_once_with("ping")
    client.close.assert_called_once()


def test_pymongo_is_mongo_ready_timeout_returns_false() -> None:
    client = mock.MagicMock()
    client.admin.command.side_effect = pymongo.errors.ServerSelectionTimeoutError("timeout")
    with mock.patch("pymongo.MongoClient", return_value=client):
        factory = _try_get_is_mongo_ready_based_on_pymongo()
        assert factory is not None
        assert factory(host="127.0.0.1", port=27017) is False


def _make_fake_motor_modules(client_factory: mock.MagicMock) -> dict[str, types.ModuleType]:
    fake_motor = types.ModuleType("motor")
    fake_motor_asyncio = types.ModuleType("motor.motor_asyncio")
    fake_motor_asyncio.AsyncIOMotorClient = client_factory  # type: ignore[attr-defined]
    fake_motor.motor_asyncio = fake_motor_asyncio  # type: ignore[attr-defined]
    return {"motor": fake_motor, "motor.motor_asyncio": fake_motor_asyncio}


def test_motor_is_mongo_ready_success() -> None:
    client = mock.MagicMock()
    client.admin.command = mock.AsyncMock(return_value={"ok": 1.0})
    client.close = mock.MagicMock()
    client_factory = mock.MagicMock(return_value=client)

    with mock.patch.dict(sys.modules, _make_fake_motor_modules(client_factory)):
        factory = _try_get_is_mongo_ready_based_on_motor()
        assert factory is not None
        assert factory(host="127.0.0.1", port=27017) is True
    client.admin.command.assert_awaited_once_with("ping")


def test_motor_is_mongo_ready_timeout_returns_false() -> None:
    client = mock.MagicMock()
    client.admin.command = mock.AsyncMock(side_effect=pymongo.errors.ServerSelectionTimeoutError("timeout"))
    client.close = mock.MagicMock()
    client_factory = mock.MagicMock(return_value=client)

    with mock.patch.dict(sys.modules, _make_fake_motor_modules(client_factory)):
        factory = _try_get_is_mongo_ready_based_on_motor()
        assert factory is not None
        assert factory(host="127.0.0.1", port=27017) is False


def test_try_get_motor_factory_returns_none_when_motor_not_installed() -> None:
    with mock.patch.dict(sys.modules, {"motor": None, "motor.motor_asyncio": None}):
        assert _try_get_is_mongo_ready_based_on_motor() is None


def test_dummy_is_mongo_ready_always_true() -> None:
    factory = _get_dummy_is_mongo_ready()
    assert factory(host="anything", port=0) is True
    assert factory(host="x.example", port=99999) is True


@pytest.mark.parametrize("port", [-1, 0, 65536])
def test_dummy_ignores_arguments(port: int) -> None:
    factory = _get_dummy_is_mongo_ready()
    assert factory(host="x", port=port) is True
