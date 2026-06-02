"""requests-specific proxy patches (used by configure())."""

from __future__ import annotations

import base64
import os
from typing import Any, Callable
from urllib.parse import urlparse

_proxies_map: dict[str, str] | None = None
_proxy_basic_header: str | None = None
_ca_bundle: str | None = None
_patched = False
_orig_session_request: Callable[..., Any] | None = None
_orig_api_request: Callable[..., Any] | None = None


def _proxy_basic_authorization(proxy_url: str) -> str | None:
    parsed = urlparse(proxy_url)
    if parsed.username:
        password = parsed.password or ""
        token = parsed.username
    else:
        token = os.environ.get("ARGUS_BUCKET_TOKEN")
        if not token:
            return None
        password = ""
    credentials = base64.b64encode(f"{token}:{password}".encode()).decode()
    return f"Basic {credentials}"


def _resolve_ca_bundle() -> str | None:
    return (
        os.environ.get("REQUESTS_CA_BUNDLE")
        or os.environ.get("SSL_CERT_FILE")
        or os.environ.get("CURL_CA_BUNDLE")
    )


def _build_proxy_map_from_env() -> dict[str, str] | None:
    https = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    http = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    url = https or http
    if not url:
        return None
    return {"http": url, "https": url}


def _prepare_argus_session(session: Any) -> None:
    if getattr(session, "_argus_prepared", False):
        return

    import requests.sessions

    if _proxies_map is not None:
        session.proxies = dict(_proxies_map)
    session.trust_env = False

    if _proxy_basic_header is not None:

        class _ArgusProxyAdapter(requests.adapters.HTTPAdapter):
            def proxy_headers(self, proxy: str) -> dict[str, str]:
                return {"Proxy-Authorization": _proxy_basic_header}

        adapter = _ArgusProxyAdapter()
        session.mount("https://", adapter)
        session.mount("http://", adapter)

    session._argus_prepared = True  # type: ignore[attr-defined]


def _inject_request_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    if _proxies_map is not None and kwargs.get("proxies") is None:
        kwargs["proxies"] = dict(_proxies_map)
    if _ca_bundle is not None and kwargs.get("verify") is None:
        kwargs["verify"] = _ca_bundle
    return kwargs


def _ensure_requests_patched() -> None:
    global _patched, _orig_session_request, _orig_api_request
    if _patched:
        return

    import requests.api as api
    import requests.sessions as sessions

    _orig_session_request = sessions.Session.request
    _orig_api_request = api.request

    def session_request(self: Any, method: str, url: str, **kwargs: Any) -> Any:
        _prepare_argus_session(self)
        return _orig_session_request(
            self, method, url, **_inject_request_kwargs(kwargs)
        )

    def api_request(method: str, url: str, **kwargs: Any) -> Any:
        return _orig_api_request(method, url, **_inject_request_kwargs(kwargs))

    sessions.Session.request = session_request  # type: ignore[method-assign]
    api.request = api_request  # type: ignore[method-assign]
    _patched = True


def apply_requests_proxy_patches() -> None:
    """Apply requests monkeypatches from current proxy env (called by configure())."""
    global _proxies_map, _proxy_basic_header, _ca_bundle

    proxy_map = _build_proxy_map_from_env()
    if proxy_map is None:
        return

    proxy_url = proxy_map.get("https") or proxy_map.get("http") or ""
    basic = _proxy_basic_authorization(proxy_url)
    if basic is None:
        return

    _proxies_map = proxy_map
    _proxy_basic_header = basic
    _ca_bundle = _resolve_ca_bundle()
    _ensure_requests_patched()


def load_proxies(
    *,
    http_proxy: str | None = None,
    https_proxy: str | None = None,
) -> bool:
    """
    Deprecated: use :func:`configure` instead.

    Applies requests patches only; does not patch ssl/aiohttp globally.
    """
    from useargus.proxy.configure import configure
    from useargus.errors import ArgusConfigureError

    try:
        configure()
        return True
    except ArgusConfigureError:
        has_proxy = bool(
            http_proxy
            or https_proxy
            or os.environ.get("HTTP_PROXY")
            or os.environ.get("HTTPS_PROXY")
            or os.environ.get("http_proxy")
            or os.environ.get("https_proxy")
        )
        if has_proxy:
            apply_requests_proxy_patches()
            return _proxies_map is not None
        return False
