"""Tests for deprecated load_proxies."""

from __future__ import annotations

import pytest

from useargus.proxy.undici import load_proxies


def test_load_proxies_warns_and_checks_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HTTPS_PROXY", raising=False)
    with pytest.warns(DeprecationWarning, match="deprecated"):
        assert load_proxies() is False


def test_load_proxies_true_when_env_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HTTPS_PROXY", "http://token@127.0.0.1:9000")
    with pytest.warns(DeprecationWarning):
        assert load_proxies() is True
