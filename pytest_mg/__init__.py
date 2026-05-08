from importlib.metadata import version as _get_version
from typing import Tuple

from .fixtures import (  # noqa
    Mongo,
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
    run_mongo,
    run_mongo_replicaset,
)

__all__: Tuple[str, ...] = (
    "Mongo",
    "run_mongo",
    "run_mongo_replicaset",
    "mongo",
    "mongo_5",
    "mongo_6",
    "mongo_7",
    "mongo_8",
    "mongo_rs",
    "mongo_5_rs",
    "mongo_6_rs",
    "mongo_7_rs",
    "mongo_8_rs",
)

__version__ = _get_version("pytest-mg")
