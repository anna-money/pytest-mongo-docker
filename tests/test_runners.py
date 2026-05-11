import sys
from typing import Any
from unittest import mock

import _pytest.outcomes
import docker
import docker.errors
import pytest

from pytest_mg.runners import _ensure_image, run_mongo, run_mongo_replicaset


def _make_mock_apiclient(container_id: str = "deadbeef") -> mock.MagicMock:
    client = mock.MagicMock(spec=docker.APIClient)
    client.create_container.return_value = {"Id": container_id}
    client.create_host_config.return_value = {}
    client.logs.return_value = b"mock container logs"
    client.inspect_image.return_value = {"Id": "sha256:abc"}
    return client


def test_ensure_image_skips_pull_when_image_present() -> None:
    client = _make_mock_apiclient()
    _ensure_image(client, "mongo:latest")
    client.inspect_image.assert_called_once_with("mongo:latest")
    client.pull.assert_not_called()


def test_ensure_image_pulls_when_image_not_found() -> None:
    client = _make_mock_apiclient()
    client.inspect_image.side_effect = docker.errors.ImageNotFound("not found")
    _ensure_image(client, "mongo:7")
    client.pull.assert_called_once_with("mongo:7")


def test_run_mongo_pytest_fail_on_readiness_timeout_and_cleanup() -> None:
    client = _make_mock_apiclient()
    with (
        mock.patch("pytest_mg.runners.docker.APIClient", return_value=client),
        mock.patch("pytest_mg.runners.is_mongo_ready", return_value=False),
        pytest.raises(_pytest.outcomes.Failed) as excinfo,
    ):
        with run_mongo("mongo:latest", ready_timeout=0.05):
            pytest.fail("should not reach yield")  # pragma: no cover

    assert "Failed to start mongo using mongo:latest" in str(excinfo.value)
    client.kill.assert_called_once()
    client.remove_container.assert_called_once_with("deadbeef", v=True)


def test_run_mongo_cleanup_on_yield_exception() -> None:
    client = _make_mock_apiclient()
    with (
        mock.patch("pytest_mg.runners.docker.APIClient", return_value=client),
        mock.patch("pytest_mg.runners.is_mongo_ready", return_value=True),
        pytest.raises(RuntimeError, match="boom"),
    ):
        with run_mongo("mongo:latest", ready_timeout=1.0):
            raise RuntimeError("boom")

    client.start.assert_called_once_with(container="deadbeef")
    client.kill.assert_called_once_with(container="deadbeef")
    client.remove_container.assert_called_once_with("deadbeef", v=True)


def test_run_mongo_yields_mongo_with_correct_host() -> None:
    client = _make_mock_apiclient()
    with (
        mock.patch("pytest_mg.runners.docker.APIClient", return_value=client),
        mock.patch("pytest_mg.runners.is_mongo_ready", return_value=True),
    ):
        with run_mongo("mongo:latest", ready_timeout=1.0) as m:
            assert m.host == "127.0.0.1"
            assert isinstance(m.port, int)
            assert m.port > 0


def test_run_mongo_replicaset_raises_when_pymongo_missing() -> None:
    with mock.patch.dict(sys.modules, {"pymongo": None, "pymongo.errors": None}):
        with pytest.raises(ImportError, match="pymongo is required"):
            with run_mongo_replicaset("mongo:latest"):
                pass  # pragma: no cover


def test_run_mongo_replicaset_pytest_fail_on_readiness_timeout() -> None:
    client = _make_mock_apiclient()
    with (
        mock.patch("pytest_mg.runners.docker.APIClient", return_value=client),
        mock.patch("pytest_mg.runners.is_mongo_ready", return_value=False),
        pytest.raises(_pytest.outcomes.Failed) as excinfo,
    ):
        with run_mongo_replicaset("mongo:latest", ready_timeout=0.05):
            pytest.fail("should not reach yield")  # pragma: no cover

    assert "Failed to start mongo using mongo:latest" in str(excinfo.value)
    # Cleanup is wrapped in contextlib.suppress; verify it still ran.
    client.kill.assert_called_once()
    client.remove_container.assert_called_once_with("deadbeef", v=True)


def test_run_mongo_replicaset_primary_election_timeout_pytest_fail() -> None:
    client = _make_mock_apiclient()
    pymongo_client = mock.MagicMock()

    def _admin_command(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "replSetInitiate":
            return {"ok": 1.0}
        if name == "hello":
            return {"isWritablePrimary": False}
        raise AssertionError(f"unexpected admin command: {name}")  # pragma: no cover

    pymongo_client.admin.command.side_effect = _admin_command

    with (
        mock.patch("pytest_mg.runners.docker.APIClient", return_value=client),
        mock.patch("pytest_mg.runners.is_mongo_ready", return_value=True),
        mock.patch("pymongo.MongoClient", return_value=pymongo_client),
        pytest.raises(_pytest.outcomes.Failed) as excinfo,
    ):
        with run_mongo_replicaset("mongo:latest", ready_timeout=0.05):
            pytest.fail("should not reach yield")  # pragma: no cover

    assert "did not become primary" in str(excinfo.value)
    pymongo_client.close.assert_called_once()
    client.kill.assert_called_once()
    client.remove_container.assert_called_once_with("deadbeef", v=True)


def test_run_mongo_replicaset_cleanup_swallows_kill_exception() -> None:
    """contextlib.suppress should swallow Docker errors during teardown."""
    client = _make_mock_apiclient()
    client.kill.side_effect = docker.errors.APIError("kill failed")
    client.remove_container.side_effect = docker.errors.APIError("remove failed")

    with (
        mock.patch("pytest_mg.runners.docker.APIClient", return_value=client),
        mock.patch("pytest_mg.runners.is_mongo_ready", return_value=False),
        pytest.raises(_pytest.outcomes.Failed),
    ):
        with run_mongo_replicaset("mongo:latest", ready_timeout=0.01):
            pytest.fail("should not reach yield")  # pragma: no cover
