"""IPC endpoint naming (session-scoped Windows named pipe)."""

from __future__ import annotations

import os
import sys

LEGACY_WINDOWS_PIPE = r"\\.\pipe\argus"

_cached_windows_pipe: str | None = None


def ipc_pipe_name() -> str:
    """Return the Argus desktop IPC endpoint for this process."""
    global _cached_windows_pipe
    if _cached_windows_pipe is not None:
        return _cached_windows_pipe
    _cached_windows_pipe = _resolve_windows_pipe_name()
    return _cached_windows_pipe


def reset_ipc_pipe_name_cache_for_tests() -> None:
    """Clear cached pipe name (tests only)."""
    global _cached_windows_pipe
    _cached_windows_pipe = None


def _resolve_windows_pipe_name() -> str:
    session_id = _windows_session_id()
    if session_id is not None and session_id > 0:
        return rf"\\.\pipe\argus-{session_id}"
    return LEGACY_WINDOWS_PIPE


def _windows_session_id() -> int | None:
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.windll.kernel32
        pid = os.getpid()
        session = wintypes.DWORD(0)
        ok = kernel32.ProcessIdToSessionId(
            wintypes.DWORD(pid),
            ctypes.byref(session),
        )
        if ok:
            return int(session.value)
    except (AttributeError, OSError, ValueError):
        return None
    return None
