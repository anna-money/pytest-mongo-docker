import socket
from contextlib import closing

from pytest_mg.utils import is_mongo_ready


def test_returns_true_when_port_open() -> None:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        host, port = server.getsockname()
        assert is_mongo_ready(host=host, port=port, timeout=0.5) is True


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
