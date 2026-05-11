import importlib
import sys
import types
from collections.abc import Iterator
from unittest import mock

import pymongo.errors
import pytest

import pytest_mg.utils
from pytest_mg.utils import (
    _get_dummy_is_mongo_ready,
    _try_get_is_mongo_ready_based_on_motor,
    _try_get_is_mongo_ready_based_on_pymongo,
)

# ---------------------------------------------------------------------------
# pymongo-based factory
# ---------------------------------------------------------------------------


def test_pymongo_success() -> None:
    client = mock.MagicMock()
    client.admin.command.return_value = {"ok": 1.0}
    with mock.patch("pymongo.MongoClient", return_value=client):
        factory = _try_get_is_mongo_ready_based_on_pymongo()
        assert factory is not None
        assert factory(host="127.0.0.1", port=27017) is True
    client.admin.command.assert_called_once_with("ping")
    client.close.assert_called_once()


def test_pymongo_timeout_returns_false() -> None:
    client = mock.MagicMock()
    client.admin.command.side_effect = pymongo.errors.ServerSelectionTimeoutError("timeout")
    with mock.patch("pymongo.MongoClient", return_value=client):
        factory = _try_get_is_mongo_ready_based_on_pymongo()
        assert factory is not None
        assert factory(host="127.0.0.1", port=27017) is False


# ---------------------------------------------------------------------------
# motor-based factory
# ---------------------------------------------------------------------------


def _make_fake_motor_modules(client_factory: mock.MagicMock) -> dict[str, types.ModuleType]:
    fake_motor = types.ModuleType("motor")
    fake_motor_asyncio = types.ModuleType("motor.motor_asyncio")
    fake_motor_asyncio.AsyncIOMotorClient = client_factory  # type: ignore[attr-defined]
    fake_motor.motor_asyncio = fake_motor_asyncio  # type: ignore[attr-defined]
    return {"motor": fake_motor, "motor.motor_asyncio": fake_motor_asyncio}


def test_motor_success() -> None:
    client = mock.MagicMock()
    client.admin.command = mock.AsyncMock(return_value={"ok": 1.0})
    client.close = mock.MagicMock()
    client_factory = mock.MagicMock(return_value=client)

    with mock.patch.dict(sys.modules, _make_fake_motor_modules(client_factory)):
        factory = _try_get_is_mongo_ready_based_on_motor()
        assert factory is not None
        assert factory(host="127.0.0.1", port=27017) is True
    client.admin.command.assert_awaited_once_with("ping")


def test_motor_timeout_returns_false() -> None:
    client = mock.MagicMock()
    client.admin.command = mock.AsyncMock(side_effect=pymongo.errors.ServerSelectionTimeoutError("timeout"))
    client.close = mock.MagicMock()
    client_factory = mock.MagicMock(return_value=client)

    with mock.patch.dict(sys.modules, _make_fake_motor_modules(client_factory)):
        factory = _try_get_is_mongo_ready_based_on_motor()
        assert factory is not None
        assert factory(host="127.0.0.1", port=27017) is False


def test_motor_factory_returns_none_when_not_installed() -> None:
    with mock.patch.dict(sys.modules, {"motor": None, "motor.motor_asyncio": None}):
        assert _try_get_is_mongo_ready_based_on_motor() is None


# ---------------------------------------------------------------------------
# dummy fallback
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("host", "port"),
    [
        ("anything", 0),
        ("x.example", 99999),
        ("x", -1),
        ("x", 65536),
    ],
)
def test_dummy_always_true(host: str, port: int) -> None:
    factory = _get_dummy_is_mongo_ready()
    assert factory(host=host, port=port) is True


# ---------------------------------------------------------------------------
# selection priority (pymongo > motor > dummy)
# ---------------------------------------------------------------------------


@pytest.fixture
def _restore_real_selection() -> Iterator[None]:
    yield
    importlib.reload(pytest_mg.utils)


def _qualname(fn: object) -> str:
    return getattr(fn, "__qualname__", "")


def test_pymongo_wins_when_present(_restore_real_selection: None) -> None:
    importlib.reload(pytest_mg.utils)
    assert "_try_get_is_mongo_ready_based_on_pymongo" in _qualname(pytest_mg.utils.is_mongo_ready)


def test_dummy_used_when_pymongo_absent(
    monkeypatch: pytest.MonkeyPatch,
    _restore_real_selection: None,
) -> None:
    # Motor's factory also imports pymongo.errors, so absent-pymongo means
    # the chain falls all the way through to the dummy fallback.
    monkeypatch.setitem(sys.modules, "pymongo", None)
    monkeypatch.setitem(sys.modules, "pymongo.errors", None)
    importlib.reload(pytest_mg.utils)
    assert "_get_dummy_is_mongo_ready" in _qualname(pytest_mg.utils.is_mongo_ready)
    assert pytest_mg.utils.is_mongo_ready(host="anything", port=0) is True
