"""Tests for proxy factories."""

from __future__ import annotations

from pathlib import Path

import pytest

from useargus.proxy.factories import anthropic_http_client
from useargus.proxy import state
from useargus.ipc.client import ProxyConfig


@pytest.fixture
def proxy(tmp_path: Path) -> ProxyConfig:
    ca = tmp_path / "ca.pem"
    ca.write_text("-----BEGIN CERTIFICATE-----\n", encoding="utf-8")
    return ProxyConfig(
        enabled=True,
        http_proxy="http://tok@127.0.0.1:9000",
        https_proxy="http://tok@127.0.0.1:9000",
        no_proxy="localhost",
        ca_bundle_path=str(ca),
    )


def test_anthropic_http_client(
    proxy: ProxyConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ssl

    monkeypatch.setattr(
        "useargus.proxy.factories.build_ssl_context",
        lambda _path: ssl.create_default_context(),
    )
    state.set_cached_proxy(proxy)
    client = anthropic_http_client(proxy, timeout=10)
    assert client._trust_env is False  # noqa: SLF001
    client.close()
