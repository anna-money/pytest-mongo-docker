import importlib
import sys
from collections.abc import Iterator
from unittest import mock

import pymongo.errors
import pytest

import pytest_mg.utils
from pytest_mg.utils import (
    _get_dummy_is_mongo_ready,
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
# selection priority (pymongo > dummy)
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
    monkeypatch.setitem(sys.modules, "pymongo", None)
    monkeypatch.setitem(sys.modules, "pymongo.errors", None)
    importlib.reload(pytest_mg.utils)
    assert "_get_dummy_is_mongo_ready" in _qualname(pytest_mg.utils.is_mongo_ready)
    assert pytest_mg.utils.is_mongo_ready(host="anything", port=0) is True
