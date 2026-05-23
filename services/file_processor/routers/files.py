"""
File upload, job status, job history, and job deletion endpoints.
Requirements: 4.1–4.6, 7.1–7.3, 13.1–13.4, 19.6, 20.4, 20.5
"""
from __future__ import annotations
import hashlib
import logging
import os
import uuid
from pathlib import Path

import magic
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from services.file_processor.auth_dep import CurrentUser, get_current_user
from services.file_processor.database import get_db
from services.file_processor.models.job import AnalysisResult, Job, JobStatus
from services.file_processor.parsers.dispatcher import ImageOnlyPDFError, UnsupportedFormatError
from services.file_processor.schemas import (
    JobListItem,
    JobListResponse,
    JobResponse,
    JobStatusResponse,
)

logger = logging.getLogger("file_processor")
router = APIRouter(prefix="/files", tags=["files"])

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/tmp/uploads"))
MAX_RESUME_MB = int(os.getenv("MAX_RESUME_SIZE_MB", "5"))
MAX_JD_MB = int(os.getenv("MAX_JD_SIZE_MB", "2"))

ALLOWED_RESUME_MIMES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
ALLOWED_JD_MIMES = ALLOWED_RESUME_MIMES | {"text/plain"}


def _validate_file(file_bytes: bytes, filename: str, allowed_mimes: set[str], max_mb: int, field: str) -> str:
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > max_mb:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"'{field}': file size {size_mb:.1f} MB exceeds the {max_mb} MB limit.",
        )
    detected_mime = magic.from_buffer(file_bytes, mime=True)
    if detected_mime not in allowed_mimes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"'{field}': unsupported file type '{detected_mime}'. Allowed: {sorted(allowed_mimes)}",
        )
    return detected_mime


@router.post("/upload", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_files(
    resume: UploadFile = File(..., description="Resume PDF or DOCX (max 5 MB)"),
    jd: UploadFile = File(..., description="Job description PDF, DOCX, or TXT (max 2 MB)"),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobResponse:
    """Upload resume and JD, validate, save, and enqueue analysis job."""
    resume_bytes = await resume.read()
    jd_bytes = await jd.read()

    resume_mime = _validate_file(resume_bytes, resume.filename or "", ALLOWED_RESUME_MIMES, MAX_RESUME_MB, "resume")
    jd_mime = _validate_file(jd_bytes, jd.filename or "", ALLOWED_JD_MIMES, MAX_JD_MB, "jd")

    # Save files
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    job_id = uuid.uuid4()
    resume_path = UPLOAD_DIR / f"{job_id}_resume_{resume.filename}"
    jd_path = UPLOAD_DIR / f"{job_id}_jd_{jd.filename}"
    resume_path.write_bytes(resume_bytes)
    jd_path.write_bytes(jd_bytes)

    # Persist job
    job = Job(
        id=job_id,
        user_id=current_user.id,
        status=JobStatus.pending,
        resume_filename=resume.filename or "resume",
        jd_filename=jd.filename or "jd",
        resume_path=str(resume_path),
        jd_path=str(jd_path),
    )
    db.add(job)
    db.commit()

    # Enqueue Celery task
    try:
        from services.celery_worker.celery_app import process_analysis_job
        process_analysis_job.delay(str(job_id))
    except Exception as e:
        logger.warning("Failed to enqueue Celery task", extra={"job_id": str(job_id), "error": str(e)})

    return JobResponse(job_id=job_id, status="pending")


@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
def get_job_status(
    job_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobStatusResponse:
    """Poll job status. Returns result payload when completed."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")

    result = None
    if job.status == JobStatus.completed:
        ar = db.query(AnalysisResult).filter(AnalysisResult.job_id == job_id).first()
        if ar:
            result = {
                "ats_score": ar.ats_score,
                "band": ar.band,
                "hybrid_similarity": ar.hybrid_similarity,
                "section_scores": ar.section_scores,
                "skill_gap": ar.skill_gap,
                "suggestions": ar.suggestions,
                "keyword_density": ar.keyword_density,
                "skill_coverage": ar.skill_coverage,
            }

    return JobStatusResponse(job_id=job_id, status=job.status.value, result=result)


@router.get("/jobs/{job_id}/result")
def get_job_result(
    job_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Fetch full analysis result for a completed job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
    if job.status != JobStatus.completed:
        raise HTTPException(status_code=404, detail="Analysis not yet completed.")

    ar = db.query(AnalysisResult).filter(AnalysisResult.job_id == job_id).first()
    if ar is None:
        raise HTTPException(status_code=404, detail="Result not found.")

    return {
        "job_id": str(job_id),
        "ats_score": ar.ats_score,
        "band": ar.band,
        "hybrid_similarity": ar.hybrid_similarity,
        "section_scores": ar.section_scores,
        "skill_gap": ar.skill_gap,
        "suggestions": ar.suggestions,
        "keyword_density": ar.keyword_density,
        "skill_coverage": ar.skill_coverage,
        "created_at": ar.created_at.isoformat(),
    }


@router.get("/jobs", response_model=JobListResponse)
def list_jobs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobListResponse:
    """Paginated list of jobs for the authenticated user."""
    total = db.query(Job).filter(Job.user_id == current_user.id).count()
    jobs = (
        db.query(Job)
        .filter(Job.user_id == current_user.id)
        .order_by(Job.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items: list[JobListItem] = []
    for job in jobs:
        ar = db.query(AnalysisResult).filter(AnalysisResult.job_id == job.id).first()
        items.append(
            JobListItem(
                job_id=job.id,
                status=job.status.value,
                resume_filename=job.resume_filename,
                jd_filename=job.jd_filename,
                created_at=job.created_at.isoformat(),
                ats_score=ar.ats_score if ar else None,
                band=ar.band if ar else None,
            )
        )

    return JobListResponse(jobs=items, total=total, page=page, page_size=page_size)


@router.delete("/jobs/{job_id}", status_code=status.HTTP_200_OK)
def delete_job(
    job_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete a job and its analysis result. Enqueues vector cleanup."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")

    db.query(AnalysisResult).filter(AnalysisResult.job_id == job_id).delete()
    db.delete(job)
    db.commit()

    try:
        from services.celery_worker.celery_app import cleanup_job_vectors
        cleanup_job_vectors.delay(str(job_id))
    except Exception as e:
        logger.warning("Failed to enqueue vector cleanup", extra={"job_id": str(job_id), "error": str(e)})
