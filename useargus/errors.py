"""Argus IPC and SDK error types."""

from __future__ import annotations

from typing import NoReturn


class ArgusError(Exception):
    """Base error for Argus client failures."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        request_id: str | None = None,
    ) -> None:
        self.code = code
        self.request_id = request_id
        super().__init__(message)

    def __str__(self) -> str:
        msg = super().__str__()
        if self.request_id:
            return f"[{self.code}] {msg} (request_id={self.request_id})"
        return f"[{self.code}] {msg}"


class ArgusConnectionError(ArgusError):
    """Socket or named pipe unavailable, or transport failed."""

    def __init__(self, message: str, *, request_id: str | None = None) -> None:
        super().__init__("CONNECTION_ERROR", message, request_id=request_id)


class ArgusLockedError(ArgusError):
    """Argus is signed out; IPC is unavailable until sign-in."""

    def __init__(self, message: str, *, request_id: str | None = None) -> None:
        super().__init__("LOCKED", message, request_id=request_id)


class ArgusDeniedError(ArgusError):
    """User denied client access (see ``denied_code``)."""

    denied_code: str

    def __init__(
        self,
        message: str,
        *,
        denied_code: str = "APPROVAL_DENIED",
        request_id: str | None = None,
    ) -> None:
        self.denied_code = denied_code
        super().__init__(denied_code, message, request_id=request_id)


class ArgusApprovalTimeoutError(ArgusDeniedError):
    """Access approval dialog timed out."""

    def __init__(self, message: str, *, request_id: str | None = None) -> None:
        super().__init__(
            message,
            denied_code="APPROVAL_TIMEOUT",
            request_id=request_id,
        )


class ArgusApprovalDeniedError(ArgusDeniedError):
    """User explicitly denied client access."""

    def __init__(self, message: str, *, request_id: str | None = None) -> None:
        super().__init__(
            message,
            denied_code="APPROVAL_DENIED",
            request_id=request_id,
        )


class ArgusBucketNotFoundError(ArgusError):
    """``ARGUS_BUCKET_ID`` does not match any bucket in Argus."""

    def __init__(self, message: str, *, request_id: str | None = None) -> None:
        super().__init__("BUCKET_NOT_FOUND", message, request_id=request_id)


class ArgusInvalidTokenError(ArgusError):
    """``ARGUS_BUCKET_TOKEN`` does not match the bucket's current token."""

    def __init__(self, message: str, *, request_id: str | None = None) -> None:
        super().__init__("INVALID_TOKEN", message, request_id=request_id)


class ArgusBucketInactiveError(ArgusError):
    """Bucket exists but is paused (not tray-active)."""

    def __init__(self, message: str, *, request_id: str | None = None) -> None:
        super().__init__("BUCKET_INACTIVE", message, request_id=request_id)


class ArgusInvalidRequestError(ArgusError):
    """Malformed IPC request JSON or fields."""

    def __init__(self, message: str, *, request_id: str | None = None) -> None:
        super().__init__("INVALID_REQUEST", message, request_id=request_id)


class ArgusPeerResolveError(ArgusError):
    """Argus could not identify the connecting process."""

    def __init__(self, message: str, *, request_id: str | None = None) -> None:
        super().__init__("PEER_RESOLVE", message, request_id=request_id)


class ArgusProxyError(ArgusError):
    """Bucket proxy misconfiguration on the Argus side."""

    def __init__(self, message: str, *, request_id: str | None = None) -> None:
        super().__init__("PROXY_ERROR", message, request_id=request_id)


class ArgusInvalidResponseError(ArgusError):
    """Argus returned an unexpected or malformed IPC response."""

    def __init__(self, message: str, *, request_id: str | None = None) -> None:
        super().__init__("INVALID_RESPONSE", message, request_id=request_id)


class ArgusConfigureError(ArgusError):
    """Proxy config unavailable or disabled for bucket."""

    def __init__(self, message: str, *, request_id: str | None = None) -> None:
        super().__init__("CONFIGURE_ERROR", message, request_id=request_id)


# Maps Argus IPC ``code`` (status=error) to exception class.
_IPC_ERROR_CLASSES: dict[str, type[ArgusError]] = {
    "BUCKET_NOT_FOUND": ArgusBucketNotFoundError,
    "NOT_FOUND": ArgusBucketNotFoundError,
    "INVALID_TOKEN": ArgusInvalidTokenError,
    "BUCKET_INACTIVE": ArgusBucketInactiveError,
    "INVALID_REQUEST": ArgusInvalidRequestError,
    "PEER_RESOLVE": ArgusPeerResolveError,
    "PROXY_ERROR": ArgusProxyError,
    "LOCKED": ArgusLockedError,
    "NOT_SIGNED_IN": ArgusLockedError,
    "SERIALIZE_ERROR": ArgusInvalidResponseError,
    "INVALID_RESPONSE": ArgusInvalidResponseError,
    "UNKNOWN_STATUS": ArgusInvalidResponseError,
    "LOCK_ERROR": ArgusError,
    "DB_ERROR": ArgusError,
    "INTERNAL_ERROR": ArgusError,
    "IPC_ERROR": ArgusError,
}


def _fallback_ipc_message(code: str) -> str:
    return {
        "BUCKET_NOT_FOUND": (
            "Bucket not found. Verify ARGUS_BUCKET_ID in your .env matches a bucket in Argus."
        ),
        "INVALID_TOKEN": (
            "Client token rejected. Regenerate the token in Argus and update ARGUS_BUCKET_TOKEN."
        ),
        "BUCKET_INACTIVE": (
            "Bucket is paused. Activate it in Argus (Buckets page or system tray)."
        ),
        "PEER_RESOLVE": (
            "Argus could not identify this process. Retry from a normal terminal or IDE."
        ),
        "PROXY_ERROR": (
            "Bucket proxy is misconfigured in Argus. Check proxy settings for this bucket."
        ),
    }.get(code, "Argus returned an error. Check that Argus is signed in and the bucket is active.")


def raise_for_ipc_response(resp: dict[str, object]) -> NoReturn:
    """Raise a typed :class:`ArgusError` subclass from an Argus IPC JSON response."""
    request_id = resp.get("request_id")
    rid = request_id if isinstance(request_id, str) else None
    status = resp.get("status")

    if status == "ok":
        raise ArgusInvalidResponseError(
            "Internal error: raise_for_ipc_response called on ok status",
            request_id=rid,
        )

    if status == "locked":
        message = resp.get("message")
        raise ArgusLockedError(
            message
            if isinstance(message, str)
            else "Argus is not signed in. Sign in to the Argus app and retry.",
            request_id=rid,
        )

    if status == "denied":
        message = resp.get("message")
        msg = (
            message
            if isinstance(message, str)
            else "Access denied. Approve this client in Argus and retry."
        )
        denied_code = resp.get("code")
        code = denied_code if isinstance(denied_code, str) else "APPROVAL_DENIED"
        if code == "APPROVAL_TIMEOUT":
            raise ArgusApprovalTimeoutError(msg, request_id=rid)
        raise ArgusApprovalDeniedError(msg, request_id=rid)

    if status == "error":
        code = resp.get("code")
        message = resp.get("message")
        code_str = code if isinstance(code, str) else "IPC_ERROR"
        msg = (
            message
            if isinstance(message, str)
            else _fallback_ipc_message(code_str)
        )
        cls = _IPC_ERROR_CLASSES.get(code_str)
        if cls is not None:
            raise cls(msg, request_id=rid)
        raise ArgusError(code_str, msg, request_id=rid)

    raise ArgusInvalidResponseError(
        f"Unexpected IPC status: {status!r}",
        request_id=rid,
    )
