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
from useargus.ipc.client import FetchBucketEnvResult, ProxyConfig, fetch_bucket_env
from useargus.proxy.config import get_proxy_config, proxy_url, require_proxy_config
from useargus.proxy.wiring import (
    argus_aiohttp_config,
    argus_anthropic_config,
    argus_httpx_config,
    argus_langchain_anthropic_config,
    argus_requests_config,
    argus_urllib_config,
    create_argus_requests_proxy_adapter,
    create_argus_requests_proxy_adapter_class,
    wire_langchain_anthropic_http_client,
)

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
    "FetchBucketEnvResult",
    "LoadEnvResult",
    "ProxyConfig",
    "argus_aiohttp_config",
    "argus_anthropic_config",
    "argus_httpx_config",
    "argus_langchain_anthropic_config",
    "argus_requests_config",
    "argus_urllib_config",
    "create_argus_requests_proxy_adapter",
    "create_argus_requests_proxy_adapter_class",
    "wire_langchain_anthropic_http_client",
    "fetch_bucket_env",
    "get_proxy_config",
    "load_env",
    "proxy_url",
    "require_proxy_config",
]

__version__ = "0.2.0"
