"""
JWT creation and decoding utilities for Auth_Service.

Requirements: 2.4, 2.5
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production-use-long-random-string")
ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
EXPIRY_HOURS: int = int(os.getenv("JWT_EXPIRY_HOURS", "24"))


def create_access_token(user_id: str, email: str) -> str:
    """
    Create a signed JWT for the given user.

    The token payload contains:
      - sub: user UUID (string)
      - email: user email
      - iat: issued-at timestamp
      - exp: expiry timestamp (24 hours from now by default)
    """
    now = datetime.now(tz=timezone.utc)
    payload: dict[str, Any] = {
        "sub": user_id,
        "email": email,
        "iat": now,
        "exp": now + timedelta(hours=EXPIRY_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT.

    Raises:
        jwt.ExpiredSignatureError  — token has expired
        jwt.InvalidTokenError      — token is malformed or signature is invalid
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
