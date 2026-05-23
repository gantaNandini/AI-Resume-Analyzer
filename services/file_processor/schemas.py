"""Pydantic schemas for File_Processor."""
from __future__ import annotations
import uuid
from pydantic import BaseModel


class JobResponse(BaseModel):
    job_id: uuid.UUID
    status: str


class JobStatusResponse(BaseModel):
    job_id: uuid.UUID
    status: str
    result: dict | None = None


class JobListItem(BaseModel):
    job_id: uuid.UUID
    status: str
    resume_filename: str
    jd_filename: str
    created_at: str
    ats_score: int | None = None
    band: str | None = None

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    jobs: list[JobListItem]
    total: int
    page: int
    page_size: int
