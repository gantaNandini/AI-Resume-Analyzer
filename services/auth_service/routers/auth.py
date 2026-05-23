"""
Authentication router — registration and login endpoints.

Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2
"""

from __future__ import annotations

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from services.auth_service.auth.jwt import create_access_token
from services.auth_service.database import get_db
from services.auth_service.models.user import User
from services.auth_service.schemas import LoginRequest, RegisterRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """
    Create a new user account.

    - Returns 201 + JWT on success.
    - Returns 409 if the email is already registered.
    - Returns 422 if validation fails (handled automatically by Pydantic).
    """
    hashed = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode()
    user = User(email=body.email, hashed_password=hashed)
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    token = create_access_token(str(user.id), user.email)
    return TokenResponse(access_token=token)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate and receive a JWT",
)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """
    Authenticate with email + password.

    - Returns 200 + JWT on success.
    - Returns 401 with a generic message on failure (no user enumeration).
    """
    _INVALID = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user = db.query(User).filter(User.email == body.email).first()
    if user is None:
        raise _INVALID

    if not bcrypt.checkpw(body.password.encode(), user.hashed_password.encode()):
        raise _INVALID

    token = create_access_token(str(user.id), user.email)
    return TokenResponse(access_token=token)
