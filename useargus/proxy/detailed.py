"""Derived Argus proxy values shared across HTTP client wiring."""

from __future__ import annotations

import base64
import os
import ssl
from dataclasses import dataclass
from urllib.parse import urlparse

from useargus.ipc.client import ProxyConfig
from useargus.proxy.config import proxy_url, require_proxy_config


@dataclass(frozen=True)
class ArgusProxyDetailed:
    """All computed proxy fields used to wire HTTP libraries after ``load_env()``."""

    proxy: ProxyConfig
    url: str
    http_proxy_url: str
    https_proxy_url: str
    ca_bundle_path: str
    no_proxy: str
    proxy_authorization: str
    connect_uri: str
    ssl_context: ssl.SSLContext


def _resolve_proxy_token(url: str) -> str:
    parsed = urlparse(url)
    token = parsed.username or os.environ.get("ARGUS_BUCKET_TOKEN")
    if not token:
        from useargus.errors import ArgusConfigureError

        raise ArgusConfigureError(
            "ARGUS_BUCKET_TOKEN is required for Argus proxy authentication."
        )
    return token


def _proxy_authorization(url: str) -> str:
    parsed = urlparse(url)
    token = _resolve_proxy_token(url)
    password = parsed.password or ""
    credentials = base64.b64encode(f"{token}:{password}".encode()).decode()
    return f"Basic {credentials}"


def _connect_uri(url: str) -> str:
    parsed = urlparse(url)
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return f"{parsed.scheme}://{parsed.hostname}:{port}"


def _build_ssl_context(ca_bundle_path: str) -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.load_verify_locations(cafile=ca_bundle_path)
    return ctx


def get_argus_proxy_detailed(proxy: ProxyConfig | None = None) -> ArgusProxyDetailed:
    """Build derived proxy material from cached config (call after ``load_env()``)."""
    cfg = proxy if proxy is not None else require_proxy_config()
    url = proxy_url(cfg)
    return ArgusProxyDetailed(
        proxy=cfg,
        url=url,
        http_proxy_url=cfg.http_proxy,
        https_proxy_url=cfg.https_proxy,
        ca_bundle_path=cfg.ca_bundle_path,
        no_proxy=cfg.no_proxy,
        proxy_authorization=_proxy_authorization(url),
        connect_uri=_connect_uri(url),
        ssl_context=_build_ssl_context(cfg.ca_bundle_path),
    )
