import importlib
import socket
import subprocess
import sys
import types
from collections.abc import Iterator
from typing import Any
from unittest import mock

import pymongo.errors
import pytest

import pytest_mg.utils
from pytest_mg.utils import (
    _get_dummy_is_mongo_ready,
    _try_get_is_mongo_ready_based_on_motor,
    _try_get_is_mongo_ready_based_on_pymongo,
    find_unused_local_port,
    resolve_docker_host,
)

# ---------------------------------------------------------------------------
# resolve_docker_host
# ---------------------------------------------------------------------------


def test_resolve_docker_host_returns_env_when_set(monkeypatch: Any) -> None:
    monkeypatch.setenv("DOCKER_HOST", "tcp://example:2375")
    with mock.patch("pytest_mg.utils.subprocess.run") as run:
        assert resolve_docker_host() == "tcp://example:2375"
    run.assert_not_called()


def test_resolve_docker_host_returns_none_when_cli_missing(monkeypatch: Any) -> None:
    monkeypatch.delenv("DOCKER_HOST", raising=False)
    with mock.patch("pytest_mg.utils.shutil.which", return_value=None):
        assert resolve_docker_host() is None


def test_resolve_docker_host_reads_active_context(monkeypatch: Any) -> None:
    monkeypatch.delenv("DOCKER_HOST", raising=False)
    completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="unix:///tmp/colima.sock\n", stderr="")
    with (
        mock.patch("pytest_mg.utils.shutil.which", return_value="/usr/bin/docker"),
        mock.patch("pytest_mg.utils.subprocess.run", return_value=completed) as run,
    ):
        assert resolve_docker_host() == "unix:///tmp/colima.sock"
    args, _ = run.call_args
    assert args[0] == ["docker", "context", "inspect", "--format", "{{.Endpoints.docker.Host}}"]


def test_resolve_docker_host_returns_none_on_empty_output(monkeypatch: Any) -> None:
    monkeypatch.delenv("DOCKER_HOST", raising=False)
    completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="\n", stderr="")
    with (
        mock.patch("pytest_mg.utils.shutil.which", return_value="/usr/bin/docker"),
        mock.patch("pytest_mg.utils.subprocess.run", return_value=completed),
    ):
        assert resolve_docker_host() is None


def test_resolve_docker_host_returns_none_on_cli_error(monkeypatch: Any) -> None:
    monkeypatch.delenv("DOCKER_HOST", raising=False)
    err = subprocess.CalledProcessError(returncode=1, cmd=["docker"])
    with (
        mock.patch("pytest_mg.utils.shutil.which", return_value="/usr/bin/docker"),
        mock.patch("pytest_mg.utils.subprocess.run", side_effect=err),
    ):
        assert resolve_docker_host() is None


def test_resolve_docker_host_returns_none_on_timeout(monkeypatch: Any) -> None:
    monkeypatch.delenv("DOCKER_HOST", raising=False)
    err = subprocess.TimeoutExpired(cmd=["docker"], timeout=5)
    with (
        mock.patch("pytest_mg.utils.shutil.which", return_value="/usr/bin/docker"),
        mock.patch("pytest_mg.utils.subprocess.run", side_effect=err),
    ):
        assert resolve_docker_host() is None


# ---------------------------------------------------------------------------
# find_unused_local_port
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# is_mongo_ready factories: pymongo / motor / dummy
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# is_mongo_ready selection priority (pymongo > motor > dummy)
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
