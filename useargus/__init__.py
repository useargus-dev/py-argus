"""Load environment variables from Argus via local IPC."""

from useargus.env.load import LoadEnvResult, load_env
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
from useargus.ipc.client import fetch_bucket_env
from useargus.proxy.configure import ConfigureResult, configure
from useargus.proxy.factories import (
    ProxyAgents,
    aiohttp_session,
    anthropic_http_client,
    create_proxy_agents,
    httpx_client,
    requests_session,
)
from useargus.proxy.undici import load_proxies

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
    "ProxyAgents",
    "aiohttp_session",
    "anthropic_http_client",
    "configure",
    "create_proxy_agents",
    "fetch_bucket_env",
    "httpx_client",
    "load_env",
    "load_proxies",
    "requests_session",
]

__version__ = "0.1.0"
