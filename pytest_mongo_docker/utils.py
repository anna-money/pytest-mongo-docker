import os
import shutil
import socket
import subprocess
from typing import Any

try:
    import pymongo as _pymongo
    import pymongo.errors as _pymongo_errors

    _HAS_PYMONGO = True
except ImportError:
    _HAS_PYMONGO = False


def is_mongo_ready(*, host: str, port: int, timeout: float = 1.0) -> bool:
    # Cheap TCP probe first — fails in microseconds while mongod is still
    # booting, avoiding the ~100ms pymongo MongoClient + topology cost on
    # every poll attempt during the warm-up window.
    try:
        with socket.create_connection((host, port), timeout=timeout):
            pass
    except OSError:
        return False

    # Socket-open only proves mongod opened its listener. When pymongo is
    # installed, verify it's actually serving wire commands.
    # directConnection=True bypasses topology discovery so this also works
    # on uninitiated replica-set nodes.
    if not _HAS_PYMONGO:
        return True

    client: _pymongo.MongoClient[Any] = _pymongo.MongoClient(
        host=host,
        port=port,
        serverSelectionTimeoutMS=int(timeout * 1000),
        directConnection=True,
    )
    try:
        client.admin.command("ping")
        return True
    except _pymongo_errors.PyMongoError:
        return False
    finally:
        client.close()


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
