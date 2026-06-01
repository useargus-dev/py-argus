"""Tests for useargus.configure."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from useargus.configure import configure
from useargus.errors import ArgusConfigureError
from useargus.ipc_client import ProxyConfig
from useargus import state


@pytest.fixture(autouse=True)
def clear_state(monkeypatch: pytest.MonkeyPatch) -> None:
    state.clear_cached_proxy()
    for key in (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "REQUESTS_CA_BUNDLE",
        "SSL_CERT_FILE",
        "ARGUS_BUCKET_ID",
        "ARGUS_BUCKET_TOKEN",
    ):
        monkeypatch.delenv(key, raising=False)


def test_configure_raises_without_proxy() -> None:
    with pytest.raises(ArgusConfigureError, match="not available"):
        configure()


def test_configure_applies_proxy_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    ca = tmp_path / "ca.pem"
    ca.write_text("-----BEGIN CERTIFICATE-----\n", encoding="utf-8")
    proxy = ProxyConfig(
        enabled=True,
        http_proxy="http://tok@127.0.0.1:9000",
        https_proxy="http://tok@127.0.0.1:9000",
        no_proxy="localhost",
        ca_bundle_path=str(ca),
    )
    state.set_cached_proxy(proxy)

    result = configure()

    assert result.proxy_enabled is True
    assert os.environ["HTTPS_PROXY"] == proxy.https_proxy
    assert os.environ["REQUESTS_CA_BUNDLE"] == str(ca)


def test_load_env_caches_proxy_without_applying(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from useargus.env import load_env
    from useargus.ipc_client import FetchBucketEnvResult

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "ARGUS_BUCKET_ID=test-id\nARGUS_BUCKET_TOKEN=test-token\n",
        encoding="utf-8",
    )
    proxy = ProxyConfig(
        enabled=True,
        http_proxy="http://tok@127.0.0.1:9000",
        https_proxy="http://tok@127.0.0.1:9000",
        no_proxy="localhost",
        ca_bundle_path="/tmp/ca.pem",
    )

    with patch(
        "useargus.env.fetch_bucket_env",
        return_value=FetchBucketEnvResult(env={"API_KEY": "x"}, proxy=proxy),
    ):
        load_env()

    assert state.get_cached_proxy() == proxy
    assert "HTTP_PROXY" not in os.environ
