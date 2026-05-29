"""Tests for useargus.env."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from useargus.env import load_env
from useargus.errors import ArgusConnectionError, ArgusLockedError


@pytest.fixture(autouse=True)
def clear_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ("ARGUS_BUCKET_ID", "ARGUS_BUCKET_TOKEN", "FOO", "BAR", "LOCAL_ONLY"):
        monkeypatch.delenv(key, raising=False)


def test_load_env_applies_dotenv_when_bucket_credentials_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("FOO=from_dotenv\n", encoding="utf-8")

    result = load_env()

    assert result.source == "dotenv"
    assert "FOO" in result.keys
    assert os.environ["FOO"] == "from_dotenv"


def test_load_env_reads_bucket_credentials_from_dotenv_before_ipc(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "ARGUS_BUCKET_ID=test-id\nARGUS_BUCKET_TOKEN=test-token\n",
        encoding="utf-8",
    )

    with patch(
        "useargus.env.fetch_bucket_env",
        side_effect=ArgusConnectionError("Argus socket not found"),
    ):
        with pytest.raises((ArgusConnectionError, ArgusLockedError)):
            load_env()


def test_dotenv_overrides_bucket_values(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "ARGUS_BUCKET_ID=test-id\nARGUS_BUCKET_TOKEN=test-token\nFOO=local\n",
        encoding="utf-8",
    )

    with patch(
        "useargus.env.fetch_bucket_env",
        return_value={"FOO": "from_bucket", "BAR": "bucket_only"},
    ):
        result = load_env()

    assert result.source == "bucket"
    assert os.environ["FOO"] == "local"
    assert os.environ["BAR"] == "bucket_only"


def test_fallback_on_locked_loads_dotenv_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "ARGUS_BUCKET_ID=test-id\nARGUS_BUCKET_TOKEN=test-token\nLOCAL_ONLY=1\n",
        encoding="utf-8",
    )

    with patch(
        "useargus.env.fetch_bucket_env",
        side_effect=ArgusLockedError("signed out"),
    ):
        with pytest.warns(UserWarning, match="loading .env only"):
            result = load_env(fallback_on_locked=True)

    assert result.source == "dotenv"
    assert os.environ["LOCAL_ONLY"] == "1"


def test_override_false_skips_existing_os_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("FOO", "already_set")
    (tmp_path / ".env").write_text("FOO=from_dotenv\n", encoding="utf-8")

    result = load_env(override=False)

    assert result.source == "dotenv"
    assert os.environ["FOO"] == "already_set"
    assert result.keys == []
