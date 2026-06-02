"""Deprecated — use :mod:`useargus.proxy.factories` instead."""

from __future__ import annotations

import warnings


def load_proxies(
    *,
    http_proxy: str | None = None,
    https_proxy: str | None = None,
) -> bool:
    """
    @deprecated Use factory helpers (:func:`requests_session`, :func:`httpx_client`, …).
    """
    warnings.warn(
        "[useargus] load_proxies() is deprecated. Use requests_session() or httpx_client().",
        DeprecationWarning,
        stacklevel=2,
    )
    import os

    has_proxy = bool(
        http_proxy
        or https_proxy
        or os.environ.get("HTTP_PROXY")
        or os.environ.get("HTTPS_PROXY")
        or os.environ.get("http_proxy")
        or os.environ.get("https_proxy")
    )
    return has_proxy
