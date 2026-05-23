"""
JWT validation dependency for File_Processor.
Replicates Auth_Service JWT logic without a service call.
Requirements: 2.4, 2.5
"""
from __future__ import annotations
import os
import uuid
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production-use-long-random-string")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

_bearer = HTTPBearer(auto_error=False)
_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired token",
    headers={"WWW-Authenticate": "Bearer"},
)


class CurrentUser:
    def __init__(self, user_id: uuid.UUID, email: str):
        self.id = user_id
        self.email = email


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> CurrentUser:
    if credentials is None:
        raise _UNAUTHORIZED
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise _UNAUTHORIZED
    except jwt.InvalidTokenError:
        raise _UNAUTHORIZED

    sub = payload.get("sub")
    email = payload.get("email", "")
    if not sub:
        raise _UNAUTHORIZED
    try:
        user_id = uuid.UUID(sub)
    except ValueError:
        raise _UNAUTHORIZED
    return CurrentUser(user_id=user_id, email=email)
