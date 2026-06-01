"""Public API surface tests."""

from useargus import (
    ArgusConfigureError,
    ArgusConnectionError,
    ArgusDeniedError,
    ArgusError,
    ArgusLockedError,
    LoadEnvResult,
    configure,
    fetch_bucket_env,
    load_env,
    load_proxies,
)


def test_public_exports() -> None:
    assert callable(load_env)
    assert callable(configure)
    assert callable(load_proxies)
    assert callable(fetch_bucket_env)
    assert issubclass(ArgusConfigureError, ArgusError)
    assert issubclass(ArgusConnectionError, ArgusError)
    assert issubclass(ArgusLockedError, ArgusError)
    assert issubclass(ArgusDeniedError, ArgusError)
    assert LoadEnvResult(source="dotenv", keys=[]).source == "dotenv"
