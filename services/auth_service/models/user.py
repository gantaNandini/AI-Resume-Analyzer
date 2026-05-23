"""
SQLAlchemy ORM model for the users table.

Requirements: 1.1, 20.1
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from services.auth_service.database import Base


class User(Base):
    """
    Represents an authenticated platform user.

    Columns:
        id            — UUID primary key (auto-generated)
        email         — unique, indexed email address
        hashed_password — bcrypt hash of the user's password
        created_at    — UTC timestamp of account creation
        updated_at    — UTC timestamp of last update (auto-updated)
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(320),  # RFC 5321 max email length
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(72),  # bcrypt output is always 60 chars; 72 gives headroom
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"
