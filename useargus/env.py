"""Load environment variables from Argus and .env files."""

from __future__ import annotations

import os
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from dotenv import dotenv_values

from useargus.errors import ArgusLockedError
from useargus.ipc_client import fetch_bucket_env
from useargus import state

LoadEnvSource = Literal["bucket", "dotenv"]


@dataclass(frozen=True)
class LoadEnvResult:
    """Result of load_env(); keys never include secret values."""

    source: LoadEnvSource
    keys: list[str]


def _resolve_env_path(path: str | None) -> Path:
    return Path.cwd() / (path or ".env")


def _read_parsed_env(env_path: Path) -> dict[str, str]:
    if not env_path.is_file():
        return {}
    raw = dotenv_values(env_path)
    return {
        key: value
        for key, value in raw.items()
        if key is not None and value is not None
    }


def _apply_to_environ(parsed: dict[str, str], override: bool) -> list[str]:
    keys: list[str] = []
    for key, value in parsed.items():
        if override or key not in os.environ:
            os.environ[key] = value
            keys.append(key)
    return keys


def _bucket_credentials(parsed: dict[str, str]) -> tuple[str | None, str | None]:
    bucket_id = os.environ.get("ARGUS_BUCKET_ID") or parsed.get("ARGUS_BUCKET_ID")
    token = os.environ.get("ARGUS_BUCKET_TOKEN") or parsed.get("ARGUS_BUCKET_TOKEN")
    return bucket_id, token


def load_env(
    *,
    path: str | None = None,
    override: bool = False,
    timeout_ms: int | None = None,
    fallback_on_locked: bool = False,
) -> LoadEnvResult:
    """
    Load environment variables into os.environ (secrets only).

    Does not enable HTTP proxy or TLS patches. Call :func:`configure` after
    ``load_env()`` when the bucket has Argus Proxy enabled.

    1. Parse .env (does not apply yet).
    2. If ARGUS_BUCKET_ID and ARGUS_BUCKET_TOKEN are set (OS env or .env),
       fetch secrets from Argus over IPC and apply them.
    3. Apply .env — duplicate keys override bucket values.
    4. Without bucket credentials, apply .env only (dotenv-style).

    Argus idle app lock does not block IPC — only sign-out returns locked.
    """
    env_path = _resolve_env_path(path)
    parsed = _read_parsed_env(env_path)
    bucket_id, token = _bucket_credentials(parsed)

    if not bucket_id or not token:
        state.set_cached_proxy(None)
        keys = _apply_to_environ(parsed, override)
        return LoadEnvResult(source="dotenv", keys=keys)

    try:
        bucket_result = fetch_bucket_env(
            bucket_id=bucket_id,
            client_token=token,
            timeout_ms=timeout_ms,
        )

        for key, value in bucket_result.env.items():
            os.environ[key] = value

        state.set_cached_proxy(bucket_result.proxy)

        keys_from_dotenv = _apply_to_environ(parsed, override=True)
        keys = list(dict.fromkeys([*bucket_result.env.keys(), *keys_from_dotenv]))
        return LoadEnvResult(source="bucket", keys=keys)
    except ArgusLockedError as exc:
        state.set_cached_proxy(None)
        if fallback_on_locked:
            warnings.warn(f"[useargus] {exc}; loading .env only", stacklevel=2)
            keys = _apply_to_environ(parsed, override)
            return LoadEnvResult(source="dotenv", keys=keys)
        raise
