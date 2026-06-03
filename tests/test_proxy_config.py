"""Tests for proxy config resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from useargus.errors import ArgusConfigureError
from useargus.ipc.client import ProxyConfig
from useargus.proxy import state
from useargus.proxy.config import get_proxy_config, proxy_url, require_proxy_config


@pytest.fixture(autouse=True)
def clear_state(monkeypatch: pytest.MonkeyPatch) -> None:
    state.clear_cached_proxy()
    for key in ("ARGUS_BUCKET_ID", "ARGUS_BUCKET_TOKEN"):
        monkeypatch.delenv(key, raising=False)


def _sample_proxy(tmp_path: Path) -> ProxyConfig:
    ca = tmp_path / "ca.pem"
    ca.write_text("-----BEGIN CERTIFICATE-----\n", encoding="utf-8")
    return ProxyConfig(
        enabled=True,
        http_proxy="http://tok@127.0.0.1:9000",
        https_proxy="http://tok@127.0.0.1:9000",
        no_proxy="localhost",
        ca_bundle_path=str(ca),
    )


def test_get_proxy_config_from_cache(tmp_path: Path) -> None:
    proxy = _sample_proxy(tmp_path)
    state.set_cached_proxy(proxy)
    assert get_proxy_config() == proxy


def test_require_proxy_config(tmp_path: Path) -> None:
    proxy = _sample_proxy(tmp_path)
    state.set_cached_proxy(proxy)
    assert require_proxy_config() == proxy


def test_require_proxy_config_raises_when_missing() -> None:
    with pytest.raises(ArgusConfigureError, match="not available"):
        require_proxy_config()


def test_require_proxy_config_raises_when_disabled(tmp_path: Path) -> None:
    proxy = ProxyConfig(
        enabled=False,
        http_proxy="",
        https_proxy="",
        no_proxy="",
        ca_bundle_path=str(tmp_path / "ca.pem"),
    )
    state.set_cached_proxy(proxy)
    with pytest.raises(ArgusConfigureError, match="disabled"):
        require_proxy_config()


def test_proxy_url_prefers_https(tmp_path: Path) -> None:
    proxy = _sample_proxy(tmp_path)
    assert proxy_url(proxy) == proxy.https_proxy
