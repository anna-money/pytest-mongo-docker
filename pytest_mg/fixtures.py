import contextlib
import dataclasses
import socket
import time
import uuid
from collections.abc import Generator
from typing import Any

import docker
import docker.errors
import pytest

from .utils import find_unused_local_port, is_mongo_ready, resolve_docker_host

LOCALHOST = "127.0.0.1"


def _ensure_image(client: docker.APIClient, image: str) -> None:
    # Skip the pull when the image is already present locally — saves the
    # round-trip to the registry on warm dev machines.
    try:
        client.inspect_image(image)
    except docker.errors.ImageNotFound:
        client.pull(image)


@dataclasses.dataclass(frozen=True)
class Mongo:
    host: str
    port: int


@contextlib.contextmanager
def run_mongo(image: str, ready_timeout: float = 30.0) -> Generator[Mongo, None, None]:
    docker_client = docker.APIClient(base_url=resolve_docker_host(), version="auto")
    _ensure_image(docker_client, image)

    unused_port = find_unused_local_port()

    mongo_data_path = "/data/db"

    container = docker_client.create_container(
        image=image,
        name=f"pytest-mongo-{uuid.uuid4()}",
        ports=[27017],
        detach=True,
        # Override the image's default CMD: --bind_ip_all is required so the
        # container's port mapping reaches mongod; --quiet trims log overhead
        # during startup.
        command=["mongod", "--bind_ip_all", "--quiet"],
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

            time.sleep(0.1)
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


@contextlib.contextmanager
def run_mongo_replicaset(
    image: str,
    replica_set: str = "rs0",
    ready_timeout: float = 60.0,
) -> Generator[Mongo, None, None]:
    try:
        import pymongo
        import pymongo.errors
    except ImportError as e:
        raise ImportError("pymongo is required for replica set fixtures. Install it with: pip install pymongo") from e

    docker_client = docker.APIClient(base_url=resolve_docker_host(), version="auto")
    _ensure_image(docker_client, image)

    port = find_unused_local_port()

    container = docker_client.create_container(
        image=image,
        name=f"pytest-mongo-rs-{uuid.uuid4()}",
        ports=[27017],
        detach=True,
        command=["mongod", "--bind_ip_all", "--replSet", replica_set, "--quiet"],
        host_config=docker_client.create_host_config(
            port_bindings={27017: (LOCALHOST, port)},
            tmpfs=["/data/db"],
        ),
    )

    try:
        docker_client.start(container=container["Id"])

        # Use a socket check rather than is_mongo_ready: pymongo's topology
        # discovery times out against an uninitiated RS-mode MongoDB instance.
        deadline = time.monotonic() + ready_timeout
        while time.monotonic() < deadline:
            try:
                with socket.create_connection((LOCALHOST, port), timeout=1.0):
                    break
            except OSError:
                time.sleep(0.1)
        else:
            container_logs = docker_client.logs(container["Id"]).decode()
            pytest.fail(f"Failed to start mongo using {image} in {ready_timeout} seconds: {container_logs}")

        # Initiate the replica set. The member host must be 127.0.0.1:27017
        # (the container-internal port) so MongoDB can reach itself for
        # internal health checks. Connect with directConnection=True to avoid
        # topology-discovery issues from the Docker port mapping.
        client: pymongo.MongoClient[Any] = pymongo.MongoClient(f"mongodb://{LOCALHOST}:{port}/", directConnection=True)
        try:
            client.admin.command(
                "replSetInitiate",
                {"_id": replica_set, "members": [{"_id": 0, "host": "127.0.0.1:27017"}]},
            )

            deadline = time.monotonic() + ready_timeout
            while time.monotonic() < deadline:
                try:
                    if client.admin.command("hello").get("isWritablePrimary"):
                        break
                except Exception:
                    pass
                time.sleep(0.1)
            else:
                pytest.fail(f"MongoDB replica set did not become primary in {ready_timeout} seconds")
        finally:
            client.close()

        yield Mongo(host=LOCALHOST, port=port)
    finally:
        with contextlib.suppress(Exception):
            docker_client.kill(container=container["Id"])
        with contextlib.suppress(Exception):
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


@pytest.fixture(scope="session")
def mongo_rs() -> Generator[Mongo, None, None]:
    with run_mongo_replicaset("mongo:latest") as mongo:
        yield mongo


@pytest.fixture(scope="session")
def mongo_5_rs() -> Generator[Mongo, None, None]:
    with run_mongo_replicaset("mongo:5") as mongo:
        yield mongo


@pytest.fixture(scope="session")
def mongo_6_rs() -> Generator[Mongo, None, None]:
    with run_mongo_replicaset("mongo:6") as mongo:
        yield mongo


@pytest.fixture(scope="session")
def mongo_7_rs() -> Generator[Mongo, None, None]:
    with run_mongo_replicaset("mongo:7") as mongo:
        yield mongo


@pytest.fixture(scope="session")
def mongo_8_rs() -> Generator[Mongo, None, None]:
    with run_mongo_replicaset("mongo:8") as mongo:
        yield mongo
