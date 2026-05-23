"""
FastAPI dependency injection for Auth_Service.

Provides get_current_user which validates the Bearer JWT on every
protected endpoint.

Requirements: 2.4, 2.5
"""

from __future__ import annotations

import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from services.auth_service.auth.jwt import decode_access_token
from services.auth_service.database import get_db
from services.auth_service.models.user import User

_bearer = HTTPBearer(auto_error=False)

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired token",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """
    Validate the Bearer JWT and return the corresponding User row.

    Raises HTTP 401 if:
      - No Authorization header is present
      - The token is expired or has an invalid signature
      - The user referenced in the token no longer exists
    """
    if credentials is None:
        raise _UNAUTHORIZED

    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise _UNAUTHORIZED
    except jwt.InvalidTokenError:
        raise _UNAUTHORIZED

    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        raise _UNAUTHORIZED

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise _UNAUTHORIZED

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise _UNAUTHORIZED

    return user
