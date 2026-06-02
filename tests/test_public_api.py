"""Public API surface tests."""

from useargus import (
    ArgusConfigureError,
    ArgusConnectionError,
    ArgusDeniedError,
    ArgusError,
    ArgusLockedError,
    LoadEnvResult,
    anthropic_http_client,
    configure,
    create_proxy_agents,
    fetch_bucket_env,
    httpx_client,
    load_env,
    load_proxies,
    requests_session,
)


def test_public_exports() -> None:
    assert callable(load_env)
    assert callable(configure)
    assert callable(load_proxies)
    assert callable(fetch_bucket_env)
    assert callable(create_proxy_agents)
    assert callable(requests_session)
    assert callable(httpx_client)
    assert callable(anthropic_http_client)
    assert issubclass(ArgusConfigureError, ArgusError)
    assert issubclass(ArgusConnectionError, ArgusError)
    assert issubclass(ArgusLockedError, ArgusError)
    assert issubclass(ArgusDeniedError, ArgusError)
    assert LoadEnvResult(source="dotenv", keys=[]).source == "dotenv"
