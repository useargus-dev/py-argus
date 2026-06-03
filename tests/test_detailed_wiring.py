"""Tests for proxy wiring exports."""

from __future__ import annotations

import ssl
from pathlib import Path

import pytest

from useargus.ipc.client import ProxyConfig
from useargus.proxy import state
from useargus.proxy.detailed import get_argus_proxy_detailed
from useargus.proxy.wiring import (
    argus_anthropic_config,
    argus_httpx_config,
    argus_langchain_anthropic_config,
    argus_requests_config,
    create_argus_requests_proxy_adapter,
)


@pytest.fixture(autouse=True)
def clear_state(monkeypatch: pytest.MonkeyPatch) -> None:
    state.clear_cached_proxy()
    monkeypatch.delenv("ARGUS_BUCKET_TOKEN", raising=False)
    monkeypatch.setattr(
        "useargus.proxy.detailed._build_ssl_context",
        lambda _path: ssl.create_default_context(),
    )


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


def test_argus_requests_config_and_adapter(tmp_path: Path) -> None:
    proxy = _sample_proxy(tmp_path)
    detailed = get_argus_proxy_detailed(proxy)
    cfg = argus_requests_config(proxy)
    assert cfg["proxies"]["https"] == detailed.url
    assert cfg["verify"] == detailed.ca_bundle_path
    assert cfg["trust_env"] is False
    adapter = create_argus_requests_proxy_adapter(proxy)
    headers = adapter.proxy_headers("http://127.0.0.1:9000")
    assert headers["Proxy-Authorization"] == detailed.proxy_authorization


def test_argus_httpx_config(tmp_path: Path) -> None:
    proxy = _sample_proxy(tmp_path)
    detailed = get_argus_proxy_detailed(proxy)
    cfg = argus_httpx_config(proxy)
    assert cfg["proxy"] == detailed.url
    assert isinstance(cfg["verify"], ssl.SSLContext)
    assert cfg["trust_env"] is False


def test_argus_httpx_config_accepts_proxy(tmp_path: Path) -> None:
    proxy = _sample_proxy(tmp_path)
    cfg = argus_httpx_config(proxy)
    assert cfg["proxy"] == proxy.https_proxy


def test_argus_anthropic_config(tmp_path: Path) -> None:
    proxy = _sample_proxy(tmp_path)
    cfg = argus_anthropic_config(proxy, timeout=30)
    assert "http_client" in cfg
    client = cfg["http_client"]
    try:
        assert client.timeout.read == 30
    finally:
        client.close()


def test_argus_langchain_anthropic_config(tmp_path: Path) -> None:
    proxy = _sample_proxy(tmp_path)
    cfg = argus_langchain_anthropic_config(proxy)
    assert "http_client" in cfg
    cfg["http_client"].close()
