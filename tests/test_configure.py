"""Tests for explicit proxy factories."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from useargus.errors import ArgusConfigureError
from useargus.ipc.client import ProxyConfig
from useargus.proxy import state
from useargus.proxy.configure import configure
from useargus.proxy.factories import create_proxy_agents, httpx_client, requests_session


@pytest.fixture(autouse=True)
def clear_state(monkeypatch: pytest.MonkeyPatch) -> None:
    state.clear_cached_proxy()
    for key in (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "REQUESTS_CA_BUNDLE",
        "ARGUS_BUCKET_ID",
        "ARGUS_BUCKET_TOKEN",
    ):
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


def test_configure_warns_without_client(tmp_path: Path) -> None:
    state.set_cached_proxy(_sample_proxy(tmp_path))
    with pytest.warns(DeprecationWarning, match="deprecated"):
        result = configure()
    assert result.proxy_enabled is True
    assert result.globals_applied is False
    assert "HTTP_PROXY" not in os.environ


def test_create_proxy_agents(tmp_path: Path) -> None:
    proxy = _sample_proxy(tmp_path)
    state.set_cached_proxy(proxy)
    agents = create_proxy_agents()
    assert agents.proxy_url == proxy.https_proxy
    assert agents.ca_bundle_path == proxy.ca_bundle_path
    assert agents.proxy_basic_header.startswith("Basic ")


def test_requests_session_explicit(tmp_path: Path) -> None:
    proxy = _sample_proxy(tmp_path)
    session = requests_session(proxy)
    assert session.proxies["https"] == proxy.https_proxy
    assert session.verify == proxy.ca_bundle_path
    assert session.trust_env is False


def test_httpx_client_explicit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ssl

    monkeypatch.setattr(
        "useargus.proxy.factories.build_ssl_context",
        lambda _path: ssl.create_default_context(),
    )
    proxy = _sample_proxy(tmp_path)
    client = httpx_client(proxy, timeout=30)
    assert client._trust_env is False  # noqa: SLF001
    client.close()


def test_configure_raises_without_proxy() -> None:
    with pytest.raises(ArgusConfigureError, match="not available"):
        configure()
