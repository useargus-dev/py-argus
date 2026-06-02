"""Deprecated configure() wrapper — prefer explicit factories."""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Any, overload

from useargus.errors import ArgusConfigureError
from useargus.proxy.config import require_proxy_config
from useargus.proxy.factories import (
    aiohttp_session,
    httpx_async_client,
    httpx_client,
    requests_session,
)

_DEPRECATION = (
    "[useargus] configure() with no arguments is deprecated and will be removed "
    "in the next major. Use explicit factories: create_proxy_agents(), "
    "requests_session(), httpx_client(), anthropic_http_client(), aiohttp_session(). "
    "See README cookbook."
)


@dataclass(frozen=True)
class ConfigureResult:
    """Result of deprecated configure(); never includes secret values."""

    proxy_enabled: bool
    globals_applied: bool
    client_configured: bool


def _configure_client(client: Any) -> Any:
    try:
        import requests

        if isinstance(client, requests.Session):
            configured = requests_session()
            client.proxies.update(configured.proxies)
            client.verify = configured.verify
            client.trust_env = False
            for scheme in ("https://", "http://"):
                adapter = configured.get_adapter(scheme)
                if adapter is not None:
                    client.mount(scheme, adapter)
            return client
    except ImportError:
        pass

    try:
        import httpx

        if isinstance(client, httpx.Client):
            return httpx_client(
                timeout=client.timeout,
                headers=dict(client.headers),
                follow_redirects=client.follow_redirects,
            )
        if isinstance(client, httpx.AsyncClient):
            return httpx_async_client(
                timeout=client.timeout,
                headers=dict(client.headers),
                follow_redirects=client.follow_redirects,
            )
    except ImportError:
        pass

    try:
        import aiohttp

        if isinstance(client, aiohttp.TCPConnector):
            from useargus.proxy.factories import aiohttp_connector

            return aiohttp_connector()
        if isinstance(client, aiohttp.ClientSession):
            return aiohttp_session()
    except ImportError:
        pass

    import ssl as ssl_mod

    if isinstance(client, ssl_mod.SSLContext):
        agents = require_proxy_config()
        client.load_verify_locations(cafile=agents.ca_bundle_path)
        return client

    raise ArgusConfigureError(
        f"configure(client) does not support {type(client).__name__}. "
        "Use requests_session(), httpx_client(), anthropic_http_client(), or aiohttp_session(). "
        "See README cookbook."
    )


@overload
def configure() -> ConfigureResult: ...


@overload
def configure(client: Any) -> Any: ...


def configure(client: Any | None = None) -> ConfigureResult | Any:
    """
    @deprecated Use explicit factory helpers instead.

    With a client, returns a configured client (no global patches).
    With no argument, warns and returns metadata only.
    """
    require_proxy_config()

    if client is None:
        warnings.warn(_DEPRECATION, DeprecationWarning, stacklevel=2)
        return ConfigureResult(
            proxy_enabled=True,
            globals_applied=False,
            client_configured=False,
        )

    return _configure_client(client)
