"""Local IPC client for Argus bucket env requests."""

from __future__ import annotations

import json
import os
import socket
import sys
import uuid
from pathlib import Path
from typing import Any

from pyargus.errors import (
    ArgusConnectionError,
    ArgusDeniedError,
    ArgusError,
    ArgusLockedError,
)

DEFAULT_TIMEOUT_MS = 130_000


def _socket_path() -> Path:
    return Path.home() / ".argus" / "argus.sock"


def _read_line_from_socket(sock: socket.socket) -> str:
    buffer = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            if buffer:
                return buffer.decode("utf-8").strip()
            raise ArgusConnectionError("connection closed without response")
        buffer += chunk
        if b"\n" in buffer:
            line, _rest = buffer.split(b"\n", 1)
            return line.decode("utf-8").strip()


def _send_unix(payload: dict[str, Any], timeout_ms: int) -> str:
    if sys.platform == "win32":
        raise ArgusConnectionError("Unix domain sockets are not supported on this platform")

    sock_path = _socket_path()
    if not sock_path.exists():
        raise ArgusConnectionError(
            f"Argus socket not found at {sock_path}. Sign in to Argus and keep the app running."
        )

    timeout_s = timeout_ms / 1000.0
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(timeout_s)
    try:
        sock.connect(str(sock_path))
        sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))
        return _read_line_from_socket(sock)
    finally:
        sock.close()


def _send_windows(payload: dict[str, Any], timeout_ms: int) -> str:
    del timeout_ms  # Named pipe open/read uses OS defaults; read timeout is best-effort.
    line = (json.dumps(payload) + "\n").encode("utf-8")
    try:
        with open(r"\\.\pipe\argus", "r+b", buffering=0) as pipe:
            pipe.write(line)
            pipe.flush()
            response = pipe.readline()
            if not response:
                raise ArgusConnectionError("connection closed without response")
            return response.decode("utf-8").strip()
    except ArgusError:
        raise
    except OSError as exc:
        raise ArgusConnectionError(
            f"{exc}. Is Argus signed in? Named pipe \\\\.\\pipe\\argus must exist."
        ) from exc


def _parse_response(raw: str) -> dict[str, str]:
    try:
        resp: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ArgusError("INVALID_RESPONSE", "Argus returned non-JSON response") from exc

    status = resp.get("status")
    if status == "ok":
        env = resp.get("env")
        if isinstance(env, dict):
            return {str(key): str(value) for key, value in env.items()}
        raise ArgusError("INVALID_RESPONSE", "Argus ok response missing env map")

    if status == "locked":
        message = resp.get("message")
        raise ArgusLockedError(
            message
            if isinstance(message, str)
            else "Argus is not signed in (IPC unavailable until sign-in)"
        )

    if status == "denied":
        message = resp.get("message")
        raise ArgusDeniedError(
            message if isinstance(message, str) else "Access denied (or approval timed out)"
        )

    if status == "error":
        code = resp.get("code")
        message = resp.get("message")
        raise ArgusError(
            code if isinstance(code, str) else "IPC_ERROR",
            message if isinstance(message, str) else "Unknown Argus IPC error",
        )

    raise ArgusError("UNKNOWN_STATUS", f"Unexpected IPC status: {status!r}")


def fetch_bucket_env(
    *,
    bucket_id: str,
    client_token: str,
    cwd: str | None = None,
    timeout_ms: int | None = None,
) -> dict[str, str]:
    """Fetch mapped environment variables for a bucket over local IPC."""
    timeout = timeout_ms if timeout_ms is not None else DEFAULT_TIMEOUT_MS
    payload = {
        "request_id": str(uuid.uuid4()),
        "bucket_id": bucket_id,
        "client_token": client_token,
        "cwd": cwd if cwd is not None else os.getcwd(),
    }

    try:
        if os.name == "nt":
            raw = _send_windows(payload, timeout)
        else:
            raw = _send_unix(payload, timeout)
    except ArgusError:
        raise
    except OSError as exc:
        hint = (
            "Is Argus signed in? Named pipe \\\\.\\pipe\\argus must exist."
            if os.name == "nt"
            else "Is Argus signed in?"
        )
        raise ArgusConnectionError(f"{exc}. {hint}") from exc
    except TimeoutError as exc:
        raise ArgusConnectionError("timed out waiting for response") from exc

    return _parse_response(raw)
