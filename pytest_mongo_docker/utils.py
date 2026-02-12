import asyncio
import socket
from typing import Any, Optional, Protocol


class IsReadyFunc(Protocol):
    def __call__(
        self,
        *,
        host: str,
        port: int,
    ) -> bool: ...


def _try_get_is_mongo_ready_based_on_pymongo() -> Optional[IsReadyFunc]:
    try:
        # noinspection PyPackageRequirements
        import pymongo
        import pymongo.errors

        def _is_mongo_ready(**params: Any) -> bool:
            try:
                client = pymongo.MongoClient(**params, serverSelectionTimeoutMS=1000)
                client.admin.command("ping")
                client.close()
                return True
            except pymongo.errors.ServerSelectionTimeoutError:
                return False

        return _is_mongo_ready
    except ImportError:
        return None


def _try_get_is_mongo_ready_based_on_motor() -> Optional[IsReadyFunc]:
    try:
        # noinspection PyPackageRequirements
        import motor.motor_asyncio
        import pymongo.errors

        def _is_mongo_ready(**params: Any) -> bool:
            async def _is_mongo_ready_async() -> bool:
                try:
                    client = motor.motor_asyncio.AsyncIOMotorClient(**params, serverSelectionTimeoutMS=1000)
                    await client.admin.command("ping")
                    client.close()
                    return True
                except pymongo.errors.ServerSelectionTimeoutError:
                    return False

            return asyncio.run(_is_mongo_ready_async())

        return _is_mongo_ready

    except ImportError:
        return None


def _get_dummy_is_mongo_ready() -> IsReadyFunc:
    def _is_mongo_ready(**_: Any) -> bool:
        return True

    return _is_mongo_ready


is_mongo_ready = (
    _try_get_is_mongo_ready_based_on_pymongo()
    or _try_get_is_mongo_ready_based_on_motor()
    or _get_dummy_is_mongo_ready()
)


def find_unused_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]  # type: ignore
