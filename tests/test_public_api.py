"""Public API surface tests."""

from useargus import (
    ArgusConnectionError,
    ArgusDeniedError,
    ArgusError,
    ArgusLockedError,
    LoadEnvResult,
    fetch_bucket_env,
    load_env,
)


def test_public_exports() -> None:
    assert callable(load_env)
    assert callable(fetch_bucket_env)
    assert issubclass(ArgusConnectionError, ArgusError)
    assert issubclass(ArgusLockedError, ArgusError)
    assert issubclass(ArgusDeniedError, ArgusError)
    assert LoadEnvResult(source="dotenv", keys=[]).source == "dotenv"
