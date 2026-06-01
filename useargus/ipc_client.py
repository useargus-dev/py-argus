"""Local IPC client for Argus bucket env requests."""

from __future__ import annotations

import json
import os
import socket
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from useargus.errors import (
    ArgusConnectionError,
    ArgusError,
    ArgusInvalidResponseError,
    raise_for_ipc_response,
)

DEFAULT_TIMEOUT_MS = 130_000


@dataclass(frozen=True)
class ProxyConfig:
    enabled: bool
    http_proxy: str
    https_proxy: str
    no_proxy: str
    ca_bundle_path: str


@dataclass(frozen=True)
class FetchBucketEnvResult:
    env: dict[str, str]
    proxy: ProxyConfig | None


def _socket_path() -> Path:
    return Path.home() / ".argus" / "argus.sock"


def _connection_hint() -> str:
    if os.name == "nt":
        return (
            "Is Argus signed in and running? The named pipe \\\\.\\pipe\\argus must exist."
        )
    sock = _socket_path()
    return (
        f"Is Argus signed in and running? Expected Unix socket at {sock}."
    )


def _read_line_from_socket(sock: socket.socket) -> str:
    buffer = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            if buffer:
                return buffer.decode("utf-8").strip()
            raise ArgusConnectionError(
                "Argus closed the connection without a response. " + _connection_hint()
            )
        buffer += chunk
        if b"\n" in buffer:
            line, _rest = buffer.split(b"\n", 1)
            return line.decode("utf-8").strip()


def _send_unix(payload: dict[str, Any], timeout_ms: int) -> str:
    if sys.platform == "win32":
        raise ArgusConnectionError(
            "Unix domain sockets are not supported on this platform. Use Windows named pipe."
        )

    sock_path = _socket_path()
    if not sock_path.exists():
        raise ArgusConnectionError(
            f"Argus socket not found at {sock_path}. {_connection_hint()}"
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
    del timeout_ms
    line = (json.dumps(payload) + "\n").encode("utf-8")
    try:
        with open(r"\\.\pipe\argus", "r+b", buffering=0) as pipe:
            pipe.write(line)
            pipe.flush()
            response = pipe.readline()
            if not response:
                raise ArgusConnectionError(
                    "Argus closed the connection without a response. " + _connection_hint()
                )
            return response.decode("utf-8").strip()
    except ArgusError:
        raise
    except OSError as exc:
        raise ArgusConnectionError(f"{exc}. {_connection_hint()}") from exc


def _parse_proxy(raw: Any) -> ProxyConfig | None:
    if not isinstance(raw, dict):
        return None
    try:
        return ProxyConfig(
            enabled=bool(raw.get("enabled")),
            http_proxy=str(raw["httpProxy"]),
            https_proxy=str(raw["httpsProxy"]),
            no_proxy=str(raw.get("noProxy", "localhost,127.0.0.1,::1")),
            ca_bundle_path=str(raw["caBundlePath"]),
        )
    except KeyError as exc:
        raise ArgusInvalidResponseError(
            f"Argus proxy block missing field: {exc}"
        ) from exc


def _parse_response(raw: str) -> FetchBucketEnvResult:
    try:
        resp: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ArgusInvalidResponseError(
            "Argus returned non-JSON response. Is the Argus app up to date?"
        ) from exc

    if not isinstance(resp, dict):
        raise ArgusInvalidResponseError("Argus IPC response must be a JSON object")

    status = resp.get("status")
    if status == "ok":
        env = resp.get("env")
        if isinstance(env, dict):
            env_map = {str(key): str(value) for key, value in env.items()}
            proxy = _parse_proxy(resp.get("proxy"))
            return FetchBucketEnvResult(env=env_map, proxy=proxy)
        raise ArgusInvalidResponseError("Argus ok response missing env map")

    raise_for_ipc_response(resp)


def apply_proxy_to_environ(proxy: ProxyConfig | None) -> None:
    if proxy is None or not proxy.enabled:
        return
    os.environ["HTTP_PROXY"] = proxy.http_proxy
    os.environ["HTTPS_PROXY"] = proxy.https_proxy
    os.environ["http_proxy"] = proxy.http_proxy
    os.environ["https_proxy"] = proxy.https_proxy
    os.environ["NO_PROXY"] = proxy.no_proxy
    os.environ["no_proxy"] = proxy.no_proxy
    os.environ["REQUESTS_CA_BUNDLE"] = proxy.ca_bundle_path
    os.environ["SSL_CERT_FILE"] = proxy.ca_bundle_path
    os.environ["CURL_CA_BUNDLE"] = proxy.ca_bundle_path


def fetch_bucket_env(
    *,
    bucket_id: str,
    client_token: str,
    cwd: str | None = None,
    timeout_ms: int | None = None,
) -> FetchBucketEnvResult:
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
        raise ArgusConnectionError(f"{exc}. {_connection_hint()}") from exc
    except TimeoutError as exc:
        raise ArgusConnectionError(
            f"Timed out after {timeout_ms}ms waiting for Argus IPC response. "
            "If this is the first connection, approve the client in Argus (up to 120s)."
        ) from exc

    return _parse_response(raw)
