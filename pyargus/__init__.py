"""Load environment variables from Argus via local IPC."""

from pyargus.errors import (
    ArgusConnectionError,
    ArgusDeniedError,
    ArgusError,
    ArgusLockedError,
)
from pyargus.ipc_client import fetch_bucket_env
from pyargus.load_env import LoadEnvResult, load_env

__all__ = [
    "ArgusConnectionError",
    "ArgusDeniedError",
    "ArgusError",
    "ArgusLockedError",
    "LoadEnvResult",
    "fetch_bucket_env",
    "load_env",
]

__version__ = "0.1.0"
