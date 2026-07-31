"""
Exceptions for the TraceMind Python SDK.
"""


class TraceMindError(Exception):
    """Base exception for all TraceMind SDK errors."""

    pass


class ConnectionError(TraceMindError):
    """Raised when the TraceMind backend server is unreachable."""

    pass


class SessionError(TraceMindError):
    """Raised when a session lifecycle operation fails."""

    pass


class ValidationError(TraceMindError):
    """Raised when event or session parameters fail client-side validation."""

    pass
