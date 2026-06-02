"""Process-wide Argus SDK state (proxy config cached from load_env)."""

from __future__ import annotations

from useargus.ipc.client import ProxyConfig

_cached_proxy: ProxyConfig | None = None


def set_cached_proxy(proxy: ProxyConfig | None) -> None:
    global _cached_proxy
    _cached_proxy = proxy


def get_cached_proxy() -> ProxyConfig | None:
    return _cached_proxy


def clear_cached_proxy() -> None:
    global _cached_proxy
    _cached_proxy = None
