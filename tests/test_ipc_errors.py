"""Tests for IPC error mapping."""

from __future__ import annotations

import pytest

from useargus.errors import (
    ArgusApprovalDeniedError,
    ArgusApprovalTimeoutError,
    ArgusBucketInactiveError,
    ArgusBucketNotFoundError,
    ArgusInvalidTokenError,
    ArgusLockedError,
    ArgusPeerResolveError,
    ArgusProxyError,
    raise_for_ipc_response,
)


def test_raises_bucket_not_found() -> None:
    with pytest.raises(ArgusBucketNotFoundError) as exc:
        raise_for_ipc_response(
            {
                "status": "error",
                "code": "BUCKET_NOT_FOUND",
                "message": "Bucket 'x' was not found.",
                "request_id": "req-1",
            }
        )
    assert exc.value.code == "BUCKET_NOT_FOUND"
    assert exc.value.request_id == "req-1"
    assert "not found" in str(exc.value).lower()


def test_raises_invalid_token() -> None:
    with pytest.raises(ArgusInvalidTokenError):
        raise_for_ipc_response(
            {
                "status": "error",
                "code": "INVALID_TOKEN",
                "message": "Client token rejected.",
            }
        )


def test_raises_bucket_inactive() -> None:
    with pytest.raises(ArgusBucketInactiveError):
        raise_for_ipc_response(
            {
                "status": "error",
                "code": "BUCKET_INACTIVE",
                "message": "Bucket 'dev' is paused.",
            }
        )


def test_raises_approval_timeout() -> None:
    with pytest.raises(ArgusApprovalTimeoutError) as exc:
        raise_for_ipc_response(
            {
                "status": "denied",
                "code": "APPROVAL_TIMEOUT",
                "message": "Timed out after 120 seconds.",
            }
        )
    assert exc.value.denied_code == "APPROVAL_TIMEOUT"


def test_raises_approval_denied() -> None:
    with pytest.raises(ArgusApprovalDeniedError) as exc:
        raise_for_ipc_response(
            {
                "status": "denied",
                "code": "APPROVAL_DENIED",
                "message": "Access denied.",
            }
        )
    assert exc.value.denied_code == "APPROVAL_DENIED"


def test_raises_locked() -> None:
    with pytest.raises(ArgusLockedError):
        raise_for_ipc_response(
            {"status": "locked", "message": "Argus is not signed in."}
        )


def test_raises_peer_resolve() -> None:
    with pytest.raises(ArgusPeerResolveError):
        raise_for_ipc_response(
            {
                "status": "error",
                "code": "PEER_RESOLVE",
                "message": "Could not identify process.",
            }
        )


def test_raises_proxy_error() -> None:
    with pytest.raises(ArgusProxyError):
        raise_for_ipc_response(
            {
                "status": "error",
                "code": "PROXY_ERROR",
                "message": "Proxy port not allocated.",
            }
        )


def test_legacy_not_found_maps_to_bucket_not_found() -> None:
    with pytest.raises(ArgusBucketNotFoundError):
        raise_for_ipc_response(
            {"status": "error", "code": "NOT_FOUND", "message": "bucket not found"}
        )
