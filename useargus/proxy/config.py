"""Shared proxy config resolution (cached by load_env)."""

from __future__ import annotations

import os

from useargus.errors import ArgusConfigureError
from useargus.ipc.client import ProxyConfig, fetch_bucket_env
from useargus.proxy.state import get_cached_proxy, set_cached_proxy


def _bucket_credentials() -> tuple[str | None, str | None]:
    return (
        os.environ.get("ARGUS_BUCKET_ID"),
        os.environ.get("ARGUS_BUCKET_TOKEN"),
    )


def get_proxy_config() -> ProxyConfig | None:
    """Proxy config cached by :func:`load_env`, or fetch when credentials are set."""
    cached = get_cached_proxy()
    if cached is not None:
        return cached

    bucket_id, token = _bucket_credentials()
    if not bucket_id or not token:
        return None

    result = fetch_bucket_env(bucket_id=bucket_id, client_token=token)
    set_cached_proxy(result.proxy)
    return result.proxy


def require_proxy_config() -> ProxyConfig:
    proxy = get_proxy_config()
    if proxy is None:
        raise ArgusConfigureError(
            "Argus proxy config is not available. Call load_env() first with valid "
            "ARGUS_BUCKET_ID and ARGUS_BUCKET_TOKEN, or ensure Argus is signed in."
        )
    if not proxy.enabled:
        raise ArgusConfigureError(
            "Argus proxy is disabled for this bucket. Enable 'Argus Proxy' in Argus "
            "bucket settings, then call load_env() again."
        )
    return proxy


def proxy_url(proxy: ProxyConfig) -> str:
    return proxy.https_proxy or proxy.http_proxy
