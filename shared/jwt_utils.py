"""
Shared JWT utilities used across services that need to validate tokens
issued by the Auth_Service.

The Auth_Service is the sole issuer; other services only need to verify.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

# ---------------------------------------------------------------------------
# Configuration — read from environment at import time so tests can patch
# ---------------------------------------------------------------------------

JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_HOURS: int = int(os.getenv("JWT_EXPIRY_HOURS", "24"))


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class TokenExpiredError(Exception):
    """Raised when a JWT has passed its expiry time."""


class TokenInvalidError(Exception):
    """Raised when a JWT cannot be decoded or has an invalid signature."""


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------


def create_access_token(
    user_id: str,
    extra_claims: dict[str, Any] | None = None,
    expiry_hours: int | None = None,
) -> str:
    """
    Create a signed JWT access token for the given user_id.

    Args:
        user_id: The UUID string of the authenticated user.
        extra_claims: Optional additional claims to embed in the payload.
        expiry_hours: Override the default expiry (JWT_EXPIRY_HOURS).

    Returns:
        A signed JWT string.
    """
    hours = expiry_hours if expiry_hours is not None else JWT_EXPIRY_HOURS
    now = datetime.now(tz=timezone.utc)
    payload: dict[str, Any] = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(hours=hours),
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT access token.

    Args:
        token: The raw JWT string (without "Bearer " prefix).

    Returns:
        The decoded payload dictionary.

    Raises:
        TokenExpiredError: If the token has expired.
        TokenInvalidError: If the token is malformed or has an invalid signature.
    """
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
        return payload
    except ExpiredSignatureError as exc:
        raise TokenExpiredError("Token has expired") from exc
    except InvalidTokenError as exc:
        raise TokenInvalidError(f"Invalid token: {exc}") from exc


def extract_user_id(token: str) -> str:
    """
    Convenience wrapper that decodes a token and returns the subject (user_id).

    Raises:
        TokenExpiredError: If the token has expired.
        TokenInvalidError: If the token is invalid.
        ValueError: If the payload does not contain a 'sub' claim.
    """
    payload = decode_access_token(token)
    user_id: str | None = payload.get("sub")
    if not user_id:
        raise TokenInvalidError("Token payload missing 'sub' claim")
    return user_id
