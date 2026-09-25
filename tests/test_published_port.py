from unittest import mock

import pytest

from pytest_mongo_docker.utils import published_port


@pytest.mark.parametrize(
    ("ports", "expected"),
    [
        ({"27017/tcp": [{"HostIp": "127.0.0.1", "HostPort": "54321"}]}, 54321),
        ({"27017/tcp": [{"HostIp": "127.0.0.1", "HostPort": "40000"}, {"HostIp": "::1", "HostPort": "40001"}]}, 40000),
    ],
)
def test_reads_what_docker_bound(ports: dict[str, list[dict[str, str]]], expected: int) -> None:
    client = mock.Mock()
    client.inspect_container.return_value = {"NetworkSettings": {"Ports": ports}}

    assert published_port(client, "container-id", 27017) == expected


@pytest.mark.parametrize("ports", [{"27017/tcp": None}, {"27017/tcp": []}, {}])
def test_fails_when_nothing_was_bound(ports: dict[str, None]) -> None:
    client = mock.Mock()
    client.inspect_container.return_value = {"NetworkSettings": {"Ports": ports}}

    with pytest.raises(RuntimeError):
        published_port(client, "container-id", 27017)
