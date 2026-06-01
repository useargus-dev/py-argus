"""Tests for useargus.proxies."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
import requests

from useargus.proxies import load_proxies


@pytest.fixture(autouse=True)
def clear_proxy_env(monkeypatch: pytest.MonkeyPatch) -> None:
    import useargus.proxies as proxies_mod
    from useargus import state

    state.clear_cached_proxy()
    proxies_mod._proxies_map = None
    proxies_mod._proxy_basic_header = None
    proxies_mod._ca_bundle = None
    for key in (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "http_proxy",
        "https_proxy",
        "REQUESTS_CA_BUNDLE",
        "ARGUS_BUCKET_TOKEN",
    ):
        monkeypatch.delenv(key, raising=False)


def test_load_proxies_returns_false_without_env() -> None:
    assert load_proxies() is False


def test_load_proxies_returns_false_without_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:9000")
    assert load_proxies() is False


def test_load_proxies_returns_true_with_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HTTPS_PROXY", "http://token@127.0.0.1:9000")
    assert load_proxies() is True


def test_load_proxies_injects_proxies_and_verify(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    proxy = "http://token@127.0.0.1:9000"
    monkeypatch.setenv("HTTPS_PROXY", proxy)
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", "/tmp/ca.pem")
    load_proxies()

    captured: list[dict[str, object]] = []

    def capture_request(self, method, url, **kwargs):
        captured.append(
            {
                "proxies": kwargs.get("proxies"),
                "verify": kwargs.get("verify"),
            }
        )
        raise RuntimeError("stop")

    import useargus.proxies as proxies_mod

    with patch.object(proxies_mod, "_orig_session_request", capture_request):
        with pytest.raises(RuntimeError, match="stop"):
            requests.get("https://example.com", timeout=1)

    assert captured[0]["proxies"] == {"http": proxy, "https": proxy}
    assert captured[0]["verify"] == "/tmp/ca.pem"


def test_load_proxies_prepares_session(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HTTPS_PROXY", "http://token@127.0.0.1:9000")
    load_proxies()

    import useargus.proxies as proxies_mod

    session = requests.Session()
    proxies_mod._prepare_argus_session(session)
    assert session.trust_env is False
    assert session.get_adapter("https://example.com") is not None

