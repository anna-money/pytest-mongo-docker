import os
import shutil
import socket
import subprocess
from typing import Any, Protocol


class IsReadyFunc(Protocol):
    def __call__(
        self,
        *,
        host: str,
        port: int,
    ) -> bool: ...


def _try_get_is_mongo_ready_based_on_pymongo() -> IsReadyFunc | None:
    try:
        # noinspection PyPackageRequirements
        import pymongo
        import pymongo.errors

        def _is_mongo_ready(**params: Any) -> bool:
            try:
                client: pymongo.MongoClient[Any] = pymongo.MongoClient(**params, serverSelectionTimeoutMS=300)
                client.admin.command("ping")
                client.close()
                return True
            except pymongo.errors.ServerSelectionTimeoutError:
                return False

        return _is_mongo_ready
    except ImportError:
        return None


def _get_dummy_is_mongo_ready() -> IsReadyFunc:
    def _is_mongo_ready(**_: Any) -> bool:
        return True

    return _is_mongo_ready


is_mongo_ready = _try_get_is_mongo_ready_based_on_pymongo() or _get_dummy_is_mongo_ready()


def find_unused_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]  # type: ignore


def resolve_docker_host() -> str | None:
    # The `docker` Python SDK doesn't read `docker context` like the CLI does.
    # Hand DOCKER_HOST to it from the active context so non-default setups
    # (Colima, custom contexts) work without the user exporting it manually.
    # No-op when the docker CLI is missing or DOCKER_HOST is already set.
    host = os.environ.get("DOCKER_HOST")
    if host:
        return host
    if shutil.which("docker") is None:
        return None
    try:
        result = subprocess.run(
            ["docker", "context", "inspect", "--format", "{{.Endpoints.docker.Host}}"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() or None
