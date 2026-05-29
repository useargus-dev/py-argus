"""Load environment variables from Argus via local IPC."""

from useargus.env import LoadEnvResult, load_env
from useargus.errors import (
    ArgusConnectionError,
    ArgusDeniedError,
    ArgusError,
    ArgusLockedError,
)
from useargus.ipc_client import fetch_bucket_env

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
