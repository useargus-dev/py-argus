"""Load environment variables from Argus via local IPC."""

from useargus.configure import ConfigureResult, configure
from useargus.env import LoadEnvResult, load_env
from useargus.errors import (
    ArgusApprovalDeniedError,
    ArgusApprovalTimeoutError,
    ArgusBucketInactiveError,
    ArgusBucketNotFoundError,
    ArgusConfigureError,
    ArgusConnectionError,
    ArgusDeniedError,
    ArgusError,
    ArgusInvalidRequestError,
    ArgusInvalidResponseError,
    ArgusInvalidTokenError,
    ArgusLockedError,
    ArgusPeerResolveError,
    ArgusProxyError,
)
from useargus.ipc_client import fetch_bucket_env
from useargus.proxies import load_proxies

__all__ = [
    "ArgusApprovalDeniedError",
    "ArgusApprovalTimeoutError",
    "ArgusBucketInactiveError",
    "ArgusBucketNotFoundError",
    "ArgusConfigureError",
    "ArgusConnectionError",
    "ArgusDeniedError",
    "ArgusError",
    "ArgusInvalidRequestError",
    "ArgusInvalidResponseError",
    "ArgusInvalidTokenError",
    "ArgusLockedError",
    "ArgusPeerResolveError",
    "ArgusProxyError",
    "ConfigureResult",
    "LoadEnvResult",
    "configure",
    "fetch_bucket_env",
    "load_env",
    "load_proxies",
]

__version__ = "0.1.0"
