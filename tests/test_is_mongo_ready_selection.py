import importlib
import sys
from collections.abc import Iterator

import pytest

import pytest_mg.utils


@pytest.fixture(autouse=True)
def _restore_real_selection() -> Iterator[None]:
    yield
    importlib.reload(pytest_mg.utils)


def _qualname(fn: object) -> str:
    return getattr(fn, "__qualname__", "")


def test_pymongo_wins_when_present() -> None:
    importlib.reload(pytest_mg.utils)
    assert "_try_get_is_mongo_ready_based_on_pymongo" in _qualname(pytest_mg.utils.is_mongo_ready)


def test_dummy_used_when_pymongo_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    # Motor's factory also imports pymongo.errors, so absent-pymongo means
    # the chain falls all the way through to the dummy fallback.
    monkeypatch.setitem(sys.modules, "pymongo", None)
    monkeypatch.setitem(sys.modules, "pymongo.errors", None)
    importlib.reload(pytest_mg.utils)
    assert "_get_dummy_is_mongo_ready" in _qualname(pytest_mg.utils.is_mongo_ready)
    assert pytest_mg.utils.is_mongo_ready(host="anything", port=0) is True
