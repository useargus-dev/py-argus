"""Configure Argus HTTP proxy and TLS trust for the current process."""

from __future__ import annotations

import os
import ssl
from dataclasses import dataclass
from typing import Any, overload

from useargus.errors import ArgusConfigureError
from useargus.ipc.client import ProxyConfig, apply_proxy_to_environ, fetch_bucket_env
from useargus.proxy.state import (
    get_cached_proxy,
    set_cached_proxy,
)
from useargus.proxy.undici import apply_requests_proxy_patches

_globals_applied = False
_ssl_patched = False
_aiohttp_patched = False
_orig_ssl_create_default_context: Any = None


@dataclass(frozen=True)
class ConfigureResult:
    """Result of configure(); never includes secret values."""

    proxy_enabled: bool
    globals_applied: bool
    client_configured: bool


def _bucket_credentials() -> tuple[str | None, str | None]:
    return (
        os.environ.get("ARGUS_BUCKET_ID"),
        os.environ.get("ARGUS_BUCKET_TOKEN"),
    )


def _resolve_proxy_config() -> ProxyConfig | None:
    cached = get_cached_proxy()
    if cached is not None:
        return cached

    bucket_id, token = _bucket_credentials()
    if not bucket_id or not token:
        return None

    result = fetch_bucket_env(bucket_id=bucket_id, client_token=token)
    set_cached_proxy(result.proxy)
    return result.proxy


def _patch_ssl_context(ca_bundle_path: str) -> None:
    global _ssl_patched, _orig_ssl_create_default_context
    if _ssl_patched:
        return

    _orig_ssl_create_default_context = ssl.create_default_context

    def _argus_create_default_context(*args: Any, **kwargs: Any) -> ssl.SSLContext:
        ctx = _orig_ssl_create_default_context(*args, **kwargs)
        ctx.load_verify_locations(cafile=ca_bundle_path)
        return ctx

    ssl.create_default_context = _argus_create_default_context  # type: ignore[assignment]
    _ssl_patched = True


def _load_real_aiohttp_module() -> Any | None:
    """Import aiohttp from site-packages (skip shadowed local .py files)."""
    import importlib.util

    spec = importlib.util.find_spec("aiohttp")
    if spec is None or not spec.origin:
        return None
    origin = spec.origin.replace("\\", "/")
    if "/site-packages/" not in origin and "/dist-packages/" not in origin:
        return None
    return importlib.import_module("aiohttp")


def _patch_aiohttp_default_trust_env() -> None:
    global _aiohttp_patched
    if _aiohttp_patched:
        return

    aiohttp = _load_real_aiohttp_module()
    if aiohttp is None or not hasattr(aiohttp, "ClientSession"):
        return

    _orig_init = aiohttp.ClientSession.__init__

    def _session_init(self: Any, *args: Any, trust_env: bool = True, **kwargs: Any) -> None:
        _orig_init(self, *args, trust_env=trust_env, **kwargs)

    aiohttp.ClientSession.__init__ = _session_init  # type: ignore[method-assign]
    _aiohttp_patched = True


def _apply_global_proxy(proxy: ProxyConfig) -> None:
    global _globals_applied
    if not proxy.enabled:
        raise ArgusConfigureError(
            "Argus proxy is disabled for this bucket. Enable it in Argus bucket settings."
        )

    apply_proxy_to_environ(proxy)
    _patch_ssl_context(proxy.ca_bundle_path)
    _patch_aiohttp_default_trust_env()
    apply_requests_proxy_patches()
    _globals_applied = True


def _build_ssl_context(ca_bundle_path: str) -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.load_verify_locations(cafile=ca_bundle_path)
    return ctx


def _proxy_url(proxy: ProxyConfig) -> str:
    return proxy.https_proxy or proxy.http_proxy


def _configure_client(client: Any, proxy: ProxyConfig) -> Any:
    proxy_url = _proxy_url(proxy)
    ca_path = proxy.ca_bundle_path

    try:
        import requests

        if isinstance(client, requests.Session):
            client.proxies.update({"http": proxy_url, "https": proxy_url})
            client.verify = ca_path
            client.trust_env = False
            return client
    except ImportError:
        pass

    try:
        import httpx

        if isinstance(client, httpx.Client):
            return httpx.Client(
                proxy=proxy_url,
                verify=ca_path,
                timeout=client.timeout,
                headers=dict(client.headers),
                follow_redirects=client.follow_redirects,
            )
        if isinstance(client, httpx.AsyncClient):
            return httpx.AsyncClient(
                proxy=proxy_url,
                verify=ca_path,
                timeout=client.timeout,
                headers=dict(client.headers),
                follow_redirects=client.follow_redirects,
            )
    except ImportError:
        pass

    try:
        import aiohttp

        ssl_ctx = _build_ssl_context(ca_path)
        if isinstance(client, aiohttp.TCPConnector):
            return aiohttp.TCPConnector(ssl=ssl_ctx)
        if isinstance(client, aiohttp.ClientSession):
            return aiohttp.ClientSession(
                trust_env=True,
                connector=aiohttp.TCPConnector(ssl=ssl_ctx),
            )
    except ImportError:
        pass

    if isinstance(client, ssl.SSLContext):
        client.load_verify_locations(cafile=ca_path)
        return client

    raise ArgusConfigureError(
        f"configure() does not support {type(client).__name__}. "
        "Supported types: requests.Session, httpx.Client, httpx.AsyncClient, "
        "aiohttp.ClientSession, aiohttp.TCPConnector, ssl.SSLContext. "
        "Call configure() with no arguments for global proxy patches only."
    )


@overload
def configure() -> ConfigureResult: ...


@overload
def configure(client: Any) -> Any: ...


def configure(client: Any | None = None) -> ConfigureResult | Any:
    """
    Enable Argus HTTP proxy and MITM CA trust for this process.

    Call after :func:`load_env` when the bucket has proxy enabled.

    With no argument, applies global patches only (env vars, ``ssl``,
    ``aiohttp`` defaults, ``requests``).

    With a client argument, applies globals and returns a configured client
    (new instance for httpx/aiohttp when immutable).
    """
    proxy = _resolve_proxy_config()
    if proxy is None:
        raise ArgusConfigureError(
            "Argus proxy config is not available. Call load_env() first with valid "
            "ARGUS_BUCKET_ID and ARGUS_BUCKET_TOKEN, or ensure Argus is signed in."
        )
    if not proxy.enabled:
        raise ArgusConfigureError(
            "Argus proxy is disabled for this bucket. Enable 'Argus Proxy' in Argus "
            "bucket settings, then call load_env() and configure() again."
        )

    _apply_global_proxy(proxy)

    if client is None:
        return ConfigureResult(
            proxy_enabled=True,
            globals_applied=True,
            client_configured=False,
        )

    return _configure_client(client, proxy)
