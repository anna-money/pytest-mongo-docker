from importlib.metadata import version as _get_version

from .fixtures import (
    mongo,
    mongo_5,
    mongo_5_rs,
    mongo_6,
    mongo_6_rs,
    mongo_7,
    mongo_7_rs,
    mongo_8,
    mongo_8_rs,
    mongo_rs,
)
from .runners import Mongo, run_mongo, run_mongo_replicaset

__all__: tuple[str, ...] = (
    "Mongo",
    "mongo",
    "mongo_5",
    "mongo_5_rs",
    "mongo_6",
    "mongo_6_rs",
    "mongo_7",
    "mongo_7_rs",
    "mongo_8",
    "mongo_8_rs",
    "mongo_rs",
    "run_mongo",
    "run_mongo_replicaset",
)

__version__ = _get_version("pytest-mg")
