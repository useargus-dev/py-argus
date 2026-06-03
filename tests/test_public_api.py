"""Public API surface tests."""

from useargus import (
    ArgusConfigureError,
    ArgusConnectionError,
    ArgusDeniedError,
    ArgusError,
    ArgusLockedError,
    FetchBucketEnvResult,
    LoadEnvResult,
    ProxyConfig,
    argus_anthropic_config,
    argus_httpx_config,
    argus_langchain_anthropic_config,
    create_argus_requests_proxy_adapter,
    fetch_bucket_env,
    get_proxy_config,
    load_env,
    proxy_url,
    require_proxy_config,
    wire_langchain_anthropic_http_client,
)


def test_public_exports() -> None:
    assert callable(load_env)
    assert callable(get_proxy_config)
    assert callable(require_proxy_config)
    assert callable(argus_httpx_config)
    assert callable(argus_anthropic_config)
    assert callable(argus_langchain_anthropic_config)
    assert callable(wire_langchain_anthropic_http_client)
    assert callable(create_argus_requests_proxy_adapter)
    assert callable(proxy_url)
    assert callable(fetch_bucket_env)
    assert not hasattr(__import__("useargus"), "get_argus_proxy_detailed")
    assert not hasattr(__import__("useargus"), "argus_proxy_wiring")
    assert issubclass(ArgusConfigureError, ArgusError)
    assert issubclass(ArgusConnectionError, ArgusError)
    assert issubclass(ArgusLockedError, ArgusError)
    assert issubclass(ArgusDeniedError, ArgusError)
    assert LoadEnvResult(source="dotenv", keys=[]).source == "dotenv"
    assert ProxyConfig(
        enabled=True,
        http_proxy="http://x",
        https_proxy="http://x",
        no_proxy="",
        ca_bundle_path="/tmp/ca.pem",
    ).enabled is True
    assert FetchBucketEnvResult(env={}, proxy=None).env == {}
