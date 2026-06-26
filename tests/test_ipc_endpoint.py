"""Tests for session-scoped Windows IPC pipe naming."""

from __future__ import annotations

import sys
from unittest.mock import patch

from useargus.ipc.endpoint import (
    LEGACY_WINDOWS_PIPE,
    ipc_pipe_name,
    reset_ipc_pipe_name_cache_for_tests,
)


def test_legacy_pipe_constant() -> None:
    assert LEGACY_WINDOWS_PIPE == r"\\.\pipe\argus"


def test_ipc_pipe_name_session_scoped_on_windows() -> None:
    if sys.platform != "win32":
        return
    reset_ipc_pipe_name_cache_for_tests()
    with patch("useargus.ipc.endpoint._windows_session_id", return_value=1):
        assert ipc_pipe_name() == r"\\.\pipe\argus-1"


def test_ipc_pipe_name_falls_back_when_session_unknown() -> None:
    reset_ipc_pipe_name_cache_for_tests()
    with patch("useargus.ipc.endpoint._windows_session_id", return_value=None):
        assert ipc_pipe_name() == LEGACY_WINDOWS_PIPE


def test_ipc_pipe_name_is_cached() -> None:
    reset_ipc_pipe_name_cache_for_tests()
    with patch("useargus.ipc.endpoint._windows_session_id", return_value=42) as lookup:
        first = ipc_pipe_name()
        second = ipc_pipe_name()
        assert first == second == r"\\.\pipe\argus-42"
        lookup.assert_called_once()
