import contextlib
import dataclasses
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
def _start_mongo_container(
    *,
    image: str,
    name_prefix: str,
    command: list[str],
    ready_timeout: float,
) -> Generator[Mongo, None, None]:
    docker_client = docker.APIClient(base_url=resolve_docker_host(), version="auto")
    _ensure_image(docker_client, image)

    port = find_unused_local_port()

    container = docker_client.create_container(
        image=image,
        name=f"{name_prefix}-{uuid.uuid4()}",
        ports=[27017],
        detach=True,
        command=command,
        host_config=docker_client.create_host_config(
            port_bindings={27017: (LOCALHOST, port)},
            tmpfs=["/data/db"],
        ),
    )

    try:
        docker_client.start(container=container["Id"])

        deadline = time.monotonic() + ready_timeout
        while time.monotonic() < deadline:
            if is_mongo_ready(host=LOCALHOST, port=port):
                break
            time.sleep(0.1)
        else:
            container_logs = docker_client.logs(container["Id"]).decode()
            pytest.fail(f"Failed to start mongo using {image} in {ready_timeout} seconds: {container_logs}")

        yield Mongo(host=LOCALHOST, port=port)
    finally:
        # Teardown is best-effort: Docker errors (network already torn down,
        # container exited non-zero) must not fail tests.
        with contextlib.suppress(Exception):
            docker_client.kill(container=container["Id"])
        with contextlib.suppress(Exception):
            docker_client.remove_container(container["Id"], v=True)


@contextlib.contextmanager
def run_mongo(image: str, ready_timeout: float = 30.0) -> Generator[Mongo, None, None]:
    # --bind_ip_all: mongod must listen on 0.0.0.0 so the Docker port
    # mapping reaches it. --quiet trims startup log overhead.
    with _start_mongo_container(
        image=image,
        name_prefix="pytest-mongo",
        command=["mongod", "--bind_ip_all", "--quiet"],
        ready_timeout=ready_timeout,
    ) as mongo:
        yield mongo


@contextlib.contextmanager
def run_mongo_replicaset(
    image: str,
    replica_set: str = "rs0",
    ready_timeout: float = 60.0,
) -> Generator[Mongo, None, None]:
    try:
        import pymongo
    except ImportError as e:
        raise ImportError("pymongo is required for replica set fixtures. Install it with: pip install pymongo") from e

    with _start_mongo_container(
        image=image,
        name_prefix="pytest-mongo-rs",
        command=["mongod", "--bind_ip_all", "--replSet", replica_set, "--quiet"],
        ready_timeout=ready_timeout,
    ) as mongo:
        # Initiate the replica set. The member host must be 127.0.0.1:27017
        # (the container-internal port) so MongoDB can reach itself for
        # internal health checks. directConnection=True avoids topology-
        # discovery issues from the Docker port mapping.
        client: pymongo.MongoClient[Any] = pymongo.MongoClient(
            f"mongodb://{LOCALHOST}:{mongo.port}/", directConnection=True
        )
        try:
            # Bootstrap the replica set with a single member. Idempotent only
            # on a fresh data dir; tmpfs gives us that on every container start.
            client.admin.command(
                "replSetInitiate",
                {"_id": replica_set, "members": [{"_id": 0, "host": "127.0.0.1:27017"}]},
            )

            deadline = time.monotonic() + ready_timeout
            while time.monotonic() < deadline:
                try:
                    # Poll node state: writes are only accepted after the
                    # member transitions to PRIMARY (isWritablePrimary=True).
                    # Election can take a few hundred ms after initiate.
                    if client.admin.command("hello").get("isWritablePrimary"):
                        break
                except Exception:
                    # `hello` can raise mid-election (NotMasterError, network
                    # reset); ignore and keep polling until the deadline.
                    pass
                time.sleep(0.1)
            else:
                pytest.fail(f"MongoDB replica set did not become primary in {ready_timeout} seconds")
        finally:
            client.close()

        yield mongo


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
