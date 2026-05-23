"""
SQLAlchemy ORM model for the jobs and analysis_results tables.
Requirements: 13.1, 20.1, 20.2
"""
from __future__ import annotations
import enum
import uuid
from datetime import datetime
from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from services.file_processor.database import Base


class JobStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        Index("ix_jobs_user_id", "user_id"),
        Index("ix_jobs_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.pending, nullable=False)
    resume_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    jd_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    resume_path: Mapped[str] = mapped_column(String(1024), nullable=True)
    jd_path: Mapped[str] = mapped_column(String(1024), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Job id={self.id} status={self.status}>"


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, unique=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    ats_score: Mapped[int] = mapped_column(nullable=False)
    band: Mapped[str] = mapped_column(String(16), nullable=False)
    hybrid_similarity: Mapped[float] = mapped_column(nullable=False)
    section_scores: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    skill_gap: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    suggestions: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    keyword_density: Mapped[float] = mapped_column(nullable=True)
    skill_coverage: Mapped[float] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
