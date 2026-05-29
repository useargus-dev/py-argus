"""Argus IPC error types."""


class ArgusError(Exception):
    """Base error for Argus client failures."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class ArgusConnectionError(ArgusError):
    """Socket or named pipe unavailable, or transport failed."""

    def __init__(self, message: str) -> None:
        super().__init__("CONNECTION_ERROR", message)


class ArgusLockedError(ArgusError):
    """Argus is signed out; IPC is unavailable until sign-in."""

    def __init__(self, message: str) -> None:
        super().__init__("LOCKED", message)


class ArgusDeniedError(ArgusError):
    """User denied access or approval timed out."""

    def __init__(self, message: str) -> None:
        super().__init__("DENIED", message)
