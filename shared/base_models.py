"""
Shared Pydantic base models and response schemas used across services.

These models define the common API contract shapes so that services
can import them without duplicating definitions.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Generic response envelope
# ---------------------------------------------------------------------------

DataT = TypeVar("DataT")


class APIResponse(BaseModel, Generic[DataT]):
    """Standard API response envelope."""

    success: bool = True
    data: DataT | None = None
    message: str = ""
    request_id: str = ""

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ErrorResponse(BaseModel):
    """Standard error response body."""

    success: bool = False
    error: str
    detail: str | None = None
    request_id: str = ""


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


class DependencyHealth(BaseModel):
    """Health status of a single dependency (e.g., database, cache)."""

    name: str
    status: str  # "connected" | "degraded" | "unavailable"
    latency_ms: float | None = None


class HealthResponse(BaseModel):
    """Response body for GET /health endpoints."""

    status: str  # "ok" | "degraded" | "unavailable"
    service: str
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    dependencies: list[DependencyHealth] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Job / task status
# ---------------------------------------------------------------------------


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobStatusResponse(BaseModel):
    """Response body for job status polling endpoints."""

    job_id: UUID
    status: JobStatus
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


class PaginatedResponse(BaseModel, Generic[DataT]):
    """Paginated list response."""

    items: list[DataT]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(arbitrary_types_allowed=True)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


class TokenResponse(BaseModel):
    """JWT token response returned after login or registration."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Token lifetime in seconds")


class UserPublic(BaseModel):
    """Public-facing user representation (no password hash)."""

    id: UUID
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
