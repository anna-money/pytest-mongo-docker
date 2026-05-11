import socket
from contextlib import closing
from unittest import mock

import pymongo.errors
import pytest

from pytest_mg import utils
from pytest_mg.utils import is_mongo_ready


def _open_listener() -> socket.socket:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    return server


def test_returns_false_when_port_closed() -> None:
    # Allocate a port, then immediately close it so the next connect fails.
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    assert is_mongo_ready(host="127.0.0.1", port=port, timeout=0.2) is False


def test_returns_false_on_unreachable_host() -> None:
    # TEST-NET-1 (192.0.2.0/24, RFC 5737) is unrouteable — connect attempts time out.
    assert is_mongo_ready(host="192.0.2.1", port=27017, timeout=0.2) is False


def test_returns_true_when_port_open_and_ping_succeeds() -> None:
    with closing(_open_listener()) as server:
        host, port = server.getsockname()
        fake_client = mock.MagicMock()
        fake_client.admin.command.return_value = {"ok": 1.0}
        with mock.patch("pytest_mg.utils._pymongo.MongoClient", return_value=fake_client):
            assert is_mongo_ready(host=host, port=port, timeout=0.5) is True
        fake_client.admin.command.assert_called_once_with("ping")
        fake_client.close.assert_called_once()


def test_returns_false_when_port_open_but_pymongo_ping_fails() -> None:
    with closing(_open_listener()) as server:
        host, port = server.getsockname()
        fake_client = mock.MagicMock()
        fake_client.admin.command.side_effect = pymongo.errors.ServerSelectionTimeoutError("timeout")
        with mock.patch("pytest_mg.utils._pymongo.MongoClient", return_value=fake_client):
            assert is_mongo_ready(host=host, port=port, timeout=0.2) is False
        fake_client.close.assert_called_once()


def test_returns_true_when_pymongo_absent_and_port_open(monkeypatch: pytest.MonkeyPatch) -> None:
    # Simulate pymongo not being installed: only the socket check runs.
    monkeypatch.setattr(utils, "_HAS_PYMONGO", False)
    with closing(_open_listener()) as server:
        host, port = server.getsockname()
        assert is_mongo_ready(host=host, port=port, timeout=0.2) is True
