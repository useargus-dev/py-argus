"""Explicit per-library Argus proxy wiring (no global monkey patches)."""

from __future__ import annotations

import base64
import os
import ssl
import warnings
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from useargus.errors import ArgusConfigureError
from useargus.ipc.client import ProxyConfig
from useargus.proxy.config import proxy_url, require_proxy_config


@dataclass(frozen=True)
class ProxyAgents:
    """Proxy URL, CA path, and Basic auth header for Argus proxy."""

    proxy_url: str
    ca_bundle_path: str
    proxy_basic_header: str


def _proxy_basic_authorization(proxy_url_str: str) -> str:
    parsed = urlparse(proxy_url_str)
    if parsed.username:
        token = parsed.username
        password = parsed.password or ""
    else:
        token = os.environ.get("ARGUS_BUCKET_TOKEN")
        if not token:
            raise ArgusConfigureError(
                "ARGUS_BUCKET_TOKEN is required for Argus proxy authentication."
            )
        password = ""
    credentials = base64.b64encode(f"{token}:{password}".encode()).decode()
    return f"Basic {credentials}"


def _build_agents(proxy: ProxyConfig) -> ProxyAgents:
    url = proxy_url(proxy)
    return ProxyAgents(
        proxy_url=url,
        ca_bundle_path=proxy.ca_bundle_path,
        proxy_basic_header=_proxy_basic_authorization(url),
    )


def create_proxy_agents(proxy: ProxyConfig | None = None) -> ProxyAgents:
    """Return proxy URL, CA path, and Proxy-Authorization header. Call after ``load_env()``."""
    return _build_agents(proxy if proxy is not None else require_proxy_config())


def build_ssl_context(ca_bundle_path: str) -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.load_verify_locations(cafile=ca_bundle_path)
    return ctx


def requests_session(proxy: ProxyConfig | None = None) -> Any:
    """New ``requests.Session`` routed through Argus proxy with explicit CA trust."""
    import requests
    import requests.adapters

    agents = create_proxy_agents(proxy)
    session = requests.Session()
    session.proxies.update({"http": agents.proxy_url, "https": agents.proxy_url})
    session.verify = agents.ca_bundle_path
    session.trust_env = False

    basic = agents.proxy_basic_header

    class _ArgusProxyAdapter(requests.adapters.HTTPAdapter):
        def proxy_headers(self, proxy: str) -> dict[str, str]:
            return {"Proxy-Authorization": basic}

    adapter = _ArgusProxyAdapter()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def httpx_client(proxy: ProxyConfig | None = None, **kwargs: Any) -> Any:
    """New ``httpx.Client`` with Argus proxy and CA bundle."""
    import httpx

    agents = create_proxy_agents(proxy)
    ctx = build_ssl_context(agents.ca_bundle_path)
    return httpx.Client(
        proxy=agents.proxy_url,
        verify=ctx,
        trust_env=False,
        **kwargs,
    )


def httpx_async_client(proxy: ProxyConfig | None = None, **kwargs: Any) -> Any:
    """New ``httpx.AsyncClient`` with Argus proxy and CA bundle."""
    import httpx

    agents = create_proxy_agents(proxy)
    ctx = build_ssl_context(agents.ca_bundle_path)
    return httpx.AsyncClient(
        proxy=agents.proxy_url,
        verify=ctx,
        trust_env=False,
        **kwargs,
    )


def anthropic_http_client(proxy: ProxyConfig | None = None, **kwargs: Any) -> Any:
    """``httpx.Client`` for ``Anthropic(http_client=...)`` / LangChain."""
    return httpx_client(proxy, **kwargs)


def aiohttp_connector(proxy: ProxyConfig | None = None) -> Any:
    """``aiohttp.TCPConnector`` with Argus CA trust (proxy via ``trust_env`` on session)."""
    import aiohttp

    agents = create_proxy_agents(proxy)
    ssl_ctx = build_ssl_context(agents.ca_bundle_path)
    return aiohttp.TCPConnector(ssl=ssl_ctx)


def aiohttp_session(proxy: ProxyConfig | None = None, **kwargs: Any) -> Any:
    """New ``aiohttp.ClientSession`` that defaults ``proxy`` on each request."""
    import aiohttp

    agents = create_proxy_agents(proxy)
    ssl_ctx = build_ssl_context(agents.ca_bundle_path)
    proxy_url_str = agents.proxy_url

    class _ArgusSession(aiohttp.ClientSession):
        async def _request(self, method: str, str_or_url: Any, **req_kwargs: Any) -> Any:
            req_kwargs.setdefault("proxy", proxy_url_str)
            return await super()._request(method, str_or_url, **req_kwargs)

    return _ArgusSession(
        connector=aiohttp.TCPConnector(ssl=ssl_ctx),
        trust_env=False,
        **kwargs,
    )


def ssl_context(proxy: ProxyConfig | None = None) -> ssl.SSLContext:
    """SSL context trusting Argus MITM CA (for ``http.client`` / custom HTTPS)."""
    agents = create_proxy_agents(proxy)
    return build_ssl_context(agents.ca_bundle_path)
