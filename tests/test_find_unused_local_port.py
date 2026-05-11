import socket

from pytest_mg.utils import find_unused_local_port


def test_returns_int_in_user_range() -> None:
    port = find_unused_local_port()
    assert isinstance(port, int)
    assert 1024 <= port <= 65535


def test_socket_is_released() -> None:
    port = find_unused_local_port()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
    finally:
        s.close()


def test_returns_distinct_ports_across_calls() -> None:
    ports = {find_unused_local_port() for _ in range(5)}
    assert len(ports) > 1
