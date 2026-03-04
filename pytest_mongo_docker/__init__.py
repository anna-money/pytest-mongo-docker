import collections
import re
import sys
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

__version__ = "0.0.4"

version = f"{__version__}, Python {sys.version}"

VersionInfo = collections.namedtuple("VersionInfo", "major minor micro release_level serial")


def _parse_version(v: str) -> VersionInfo:
    version_re = r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<micro>\d+)" r"((?P<release_level>[a-z]+)(?P<serial>\d+)?)?$"
    match = re.match(version_re, v)
    if not match:
        raise ImportError(f"Invalid package version {v}")
    try:
        major = int(match.group("major"))
        minor = int(match.group("minor"))
        micro = int(match.group("micro"))
        levels = {"rc": "candidate", "a": "alpha", "b": "beta", None: "final"}
        release_level = levels[match.group("release_level")]
        serial = int(match.group("serial")) if match.group("serial") else 0
        return VersionInfo(major, minor, micro, release_level, serial)
    except Exception as e:
        raise ImportError(f"Invalid package version {v}") from e


version_info = _parse_version(__version__)
