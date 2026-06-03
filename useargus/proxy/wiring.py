"""Per-library proxy kwargs and small wiring helpers."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from useargus.ipc.client import ProxyConfig
from useargus.proxy.detailed import get_argus_proxy_detailed


def _detailed(proxy: ProxyConfig | None = None):
    return get_argus_proxy_detailed(proxy)


def argus_requests_config(
    proxy: ProxyConfig | None = None,
) -> dict[str, Any]:
    """Kwargs for ``requests.Session``.

    Mount :func:`create_argus_requests_proxy_adapter` on the session separately.
    """
    d = _detailed(proxy)
    return {
        "proxies": {"http": d.url, "https": d.url},
        "verify": d.ca_bundle_path,
        "trust_env": False,
    }


def argus_httpx_config(
    proxy: ProxyConfig | None = None,
) -> dict[str, Any]:
    """Kwargs for ``httpx.Client`` / ``httpx.AsyncClient``."""
    d = _detailed(proxy)
    return {
        "proxy": d.url,
        "verify": d.ssl_context,
        "trust_env": False,
    }


def argus_aiohttp_config(
    proxy: ProxyConfig | None = None,
) -> dict[str, Any]:
    """Values for ``aiohttp.ClientSession`` + per-request ``proxy=``."""
    d = _detailed(proxy)
    return {
        "proxy": d.url,
        "trust_env": False,
        "connector_ssl": d.ssl_context,
    }


def argus_urllib_config(
    proxy: ProxyConfig | None = None,
) -> dict[str, Any]:
    """Values for ``urllib.request.ProxyHandler`` + ``HTTPSHandler``."""
    d = _detailed(proxy)
    return {
        "proxy_handler": {"http": d.url, "https": d.url},
        "ssl_context": d.ssl_context,
    }


def create_argus_requests_proxy_adapter_class(
    proxy: ProxyConfig | None = None,
) -> type:
    """Return a ``requests`` HTTPAdapter class that sends Argus ``Proxy-Authorization``."""
    import requests.adapters

    d = _detailed(proxy)
    basic = d.proxy_authorization

    class ArgusRequestsProxyAdapter(requests.adapters.HTTPAdapter):
        def proxy_headers(self, proxy: str) -> dict[str, str]:
            return {"Proxy-Authorization": basic}

    return ArgusRequestsProxyAdapter


def create_argus_requests_proxy_adapter(
    proxy: ProxyConfig | None = None,
) -> Any:
    """Return a mounted-ready ``requests`` HTTPAdapter instance."""
    return create_argus_requests_proxy_adapter_class(proxy)()


def argus_anthropic_config(
    proxy: ProxyConfig | None = None,
    *,
    timeout: float = 60,
) -> dict[str, Any]:
    """Kwargs for ``anthropic.Anthropic`` / ``AsyncAnthropic`` (``http_client=``)."""
    import httpx

    return {
        "http_client": httpx.Client(**argus_httpx_config(proxy), timeout=timeout),
    }


def argus_langchain_anthropic_config(
    proxy: ProxyConfig | None = None,
    *,
    timeout: float = 60,
) -> dict[str, Any]:
    """``http_client`` for LangChain's Anthropic stack (``Anthropic(http_client=...)``)."""
    return argus_anthropic_config(proxy, timeout=timeout)


def wire_langchain_anthropic_http_client(http_client: Any) -> None:
    """Patch langchain-anthropic to use a fixed ``httpx`` client (sync + async factories)."""
    import langchain_anthropic._client_utils as lc_client_utils

    @lru_cache
    def _default_sync_client(
        *,
        base_url: str | None,
        timeout: Any = lc_client_utils._NOT_GIVEN,
        anthropic_proxy: str | None = None,
    ) -> Any:
        return http_client

    @lru_cache
    def _default_async_client(
        *,
        base_url: str | None,
        timeout: Any = lc_client_utils._NOT_GIVEN,
        anthropic_proxy: str | None = None,
    ) -> Any:
        return http_client

    lc_client_utils._get_default_httpx_client = _default_sync_client
    lc_client_utils._get_default_async_httpx_client = _default_async_client
