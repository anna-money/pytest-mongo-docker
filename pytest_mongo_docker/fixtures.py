import contextlib
import dataclasses
import os
import time
import uuid
from typing import Generator

import docker
import pytest

from .utils import find_unused_local_port, is_mongo_ready

LOCALHOST = "127.0.0.1"


@dataclasses.dataclass(frozen=True)
class Mongo:
    host: str
    port: int


@contextlib.contextmanager
def run_mongo(image: str, ready_timeout: float = 30.0) -> Generator[Mongo, None, None]:
    docker_client = docker.APIClient(base_url=os.getenv("DOCKER_HOST"), version="auto")
    try:
        docker_client.inspect_image(image)
    except Exception:
        docker_client.pull(image)

    unused_port = find_unused_local_port()

    mongo_data_path = "/data/db"

    container = docker_client.create_container(
        image=image,
        name=f"pytest-mongo-{uuid.uuid4()}",
        ports=[27017],
        detach=True,
        host_config=docker_client.create_host_config(
            port_bindings={27017: (LOCALHOST, unused_port)}, tmpfs=[mongo_data_path]
        ),
    )

    try:
        docker_client.start(container=container["Id"])

        started_at = time.time()

        while time.time() - started_at < ready_timeout:
            if is_mongo_ready(
                host=LOCALHOST,
                port=unused_port,
            ):
                break

            time.sleep(0.5)
        else:
            container_logs = docker_client.logs(container["Id"]).decode()
            pytest.fail(f"Failed to start mongo using {image} in {ready_timeout} seconds: {container_logs}")

        yield Mongo(
            host=LOCALHOST,
            port=unused_port,
        )
    finally:
        docker_client.kill(container=container["Id"])
        docker_client.remove_container(container["Id"], v=True)


@pytest.fixture(scope="session")
def mongo() -> Generator[Mongo, None, None]:
    with run_mongo("mongo:latest") as mongo:
        yield mongo


@pytest.fixture(scope="session")
def mongo_5() -> Generator[Mongo, None, None]:
    with run_mongo("mongo:5") as mongo:
        yield mongo


@pytest.fixture(scope="session")
def mongo_6() -> Generator[Mongo, None, None]:
    with run_mongo("mongo:6") as mongo:
        yield mongo


@pytest.fixture(scope="session")
def mongo_7() -> Generator[Mongo, None, None]:
    with run_mongo("mongo:7") as mongo:
        yield mongo


@pytest.fixture(scope="session")
def mongo_8() -> Generator[Mongo, None, None]:
    with run_mongo("mongo:8") as mongo:
        yield mongo
