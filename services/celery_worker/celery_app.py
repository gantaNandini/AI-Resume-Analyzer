"""
Celery application and task definitions.
Requirements: 13.2, 13.5, 16.5
"""
from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone

import httpx
from celery import Celery
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

logger = logging.getLogger("celery_worker")

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672//")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/resume_db")
NLP_PIPELINE_URL = os.getenv("NLP_PIPELINE_URL", "http://nlp_pipeline:8003")
SCORING_ENGINE_URL = os.getenv("SCORING_ENGINE_URL", "http://scoring_engine:8004")
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://llm_service:8005")

app = Celery(
    "resume_platform",
    broker=RABBITMQ_URL,
    backend=REDIS_URL,
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
)

# DB setup
_engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)
_Session = sessionmaker(bind=_engine, autocommit=False, autoflush=False, expire_on_commit=False)


def _get_db():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


def _update_job_status(job_id: str, status: str, failure_reason: str | None = None) -> None:
    """Update job status in PostgreSQL."""
    from services.file_processor.models.job import Job, JobStatus
    db = _Session()
    try:
        job = db.query(Job).filter(Job.id == uuid.UUID(job_id)).first()
        if job:
            job.status = JobStatus(status)
            if failure_reason:
                job.failure_reason = failure_reason
            db.commit()
    except Exception as e:
        logger.error("Failed to update job status", extra={"job_id": job_id, "error": str(e)})
        db.rollback()
    finally:
        db.close()


def _persist_result(job_id: str, user_id: str, result: dict) -> None:
    """Persist analysis result to PostgreSQL."""
    from services.file_processor.models.job import AnalysisResult, Job, JobStatus
    db = _Session()
    try:
        # Idempotent: delete existing result if any
        db.query(AnalysisResult).filter(AnalysisResult.job_id == uuid.UUID(job_id)).delete()
        ar = AnalysisResult(
            job_id=uuid.UUID(job_id),
            user_id=uuid.UUID(user_id),
            ats_score=result.get("ats_score", 0),
            band=result.get("band", "Poor"),
            hybrid_similarity=result.get("hybrid_similarity", 0.0),
            section_scores=result.get("section_scores", {}),
            skill_gap=result.get("skill_gap", {}),
            suggestions=result.get("suggestions", {}),
            keyword_density=result.get("keyword_density", 0.0),
            skill_coverage=result.get("skill_coverage", 0.0),
        )
        db.add(ar)
        job = db.query(Job).filter(Job.id == uuid.UUID(job_id)).first()
        if job:
            job.status = JobStatus.completed
        db.commit()
    except Exception as e:
        logger.error("Failed to persist result", extra={"job_id": job_id, "error": str(e)})
        db.rollback()
    finally:
        db.close()


@app.task(
    bind=True,
    name="process_analysis_job",
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def process_analysis_job(self, job_id: str) -> dict:
    """
    Full AI pipeline task:
    1. Load file paths from DB
    2. Parse documents
    3. NLP preprocess + skill extract + embed
    4. Score (ATS, hybrid similarity, skill gap)
    5. LLM suggestions
    6. Persist result
    """
    from services.file_processor.models.job import Job, JobStatus
    from services.file_processor.parsers.dispatcher import parse_document

    logger.info("Starting analysis job", extra={"job_id": job_id})
    _update_job_status(job_id, "processing")

    db = _Session()
    try:
        job = db.query(Job).filter(Job.id == uuid.UUID(job_id)).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")
        user_id = str(job.user_id)
        resume_path = job.resume_path
        jd_path = job.jd_path
    finally:
        db.close()

    # --- Step 1: Parse documents ---
    import magic
    with open(resume_path, "rb") as f:
        resume_bytes = f.read()
    with open(jd_path, "rb") as f:
        jd_bytes = f.read()

    resume_mime = magic.from_buffer(resume_bytes, mime=True)
    jd_mime = magic.from_buffer(jd_bytes, mime=True)
    resume_text = parse_document(resume_bytes, resume_mime)
    jd_text = parse_document(jd_bytes, jd_mime)

    timeout = httpx.Timeout(60.0)

    with httpx.Client(timeout=timeout) as client:
        # --- Step 2: NLP Preprocess ---
        r = client.post(f"{NLP_PIPELINE_URL}/nlp/preprocess", json={
            "text": resume_text, "document_type": "resume", "job_id": job_id
        })
        r.raise_for_status()
        resume_doc = r.json()

        r = client.post(f"{NLP_PIPELINE_URL}/nlp/preprocess", json={
            "text": jd_text, "document_type": "jd", "job_id": job_id
        })
        r.raise_for_status()
        jd_doc = r.json()

        # --- Step 3: Skill Extraction ---
        r = client.post(f"{NLP_PIPELINE_URL}/nlp/extract-skills", json={
            "document": resume_doc, "document_type": "resume"
        })
        r.raise_for_status()
        resume_skills = r.json()

        r = client.post(f"{NLP_PIPELINE_URL}/nlp/extract-skills", json={
            "document": jd_doc, "document_type": "jd"
        })
        r.raise_for_status()
        jd_skills = r.json()

        # --- Step 4: Embeddings ---
        r = client.post(f"{NLP_PIPELINE_URL}/nlp/embed", json={
            "text": resume_text, "job_id": job_id, "doc_type": "resume",
            "user_id": user_id, "sections": resume_doc.get("sections", {})
        })
        r.raise_for_status()
        resume_embeddings = r.json()

        r = client.post(f"{NLP_PIPELINE_URL}/nlp/embed", json={
            "text": jd_text, "job_id": job_id, "doc_type": "jd",
            "user_id": user_id, "sections": jd_doc.get("sections", {})
        })
        r.raise_for_status()
        jd_embeddings = r.json()

        # --- Step 5: ATS Score ---
        r = client.post(f"{SCORING_ENGINE_URL}/scoring/ats-score", json={
            "resume_embedding": resume_embeddings["full_document"],
            "jd_embedding": jd_embeddings["full_document"],
            "resume_section_embeddings": resume_embeddings.get("sections", {}),
            "jd_section_embeddings": jd_embeddings.get("sections", {}),
            "resume_tokens": resume_doc.get("tokens", []),
            "jd_tokens": jd_doc.get("tokens", []),
            "resume_skills": resume_skills,
            "jd_skills": jd_skills,
            "resume_text": resume_text,
            "jd_text": jd_text,
        })
        r.raise_for_status()
        ats_result = r.json()

        # --- Step 6: Skill Gap ---
        r = client.post(f"{SCORING_ENGINE_URL}/scoring/skill-gap", json={
            "resume_skills": resume_skills,
            "jd_skills": jd_skills,
        })
        r.raise_for_status()
        skill_gap = r.json()

        # --- Step 7: LLM Suggestions ---
        suggestions_result = {"suggestions": [], "available": False}
        try:
            r = client.post(f"{LLM_SERVICE_URL}/llm/suggestions", json={
                "ats_result": ats_result,
                "skill_gap": skill_gap,
                "resume_text": resume_text[:4000],
                "jd_text": jd_text[:4000],
            }, timeout=35.0)
            r.raise_for_status()
            suggestions_result = r.json()
        except Exception as e:
            logger.warning("LLM suggestions unavailable", extra={"job_id": job_id, "error": str(e)})

    result = {
        "ats_score": ats_result.get("score", 0),
        "band": ats_result.get("band", "Poor"),
        "hybrid_similarity": ats_result.get("hybrid_similarity", 0.0),
        "section_scores": ats_result.get("section_scores", {}),
        "keyword_density": ats_result.get("keyword_density", 0.0),
        "skill_coverage": ats_result.get("skill_coverage", 0.0),
        "skill_gap": skill_gap,
        "suggestions": suggestions_result,
    }

    _persist_result(job_id, user_id, result)
    logger.info("Analysis job completed", extra={"job_id": job_id, "ats_score": result["ats_score"]})
    return result


@app.task(name="cleanup_job_vectors", bind=True, max_retries=3)
def cleanup_job_vectors(self, job_id: str) -> None:
    """Delete Qdrant vectors for a deleted job."""
    try:
        with httpx.Client(timeout=30.0) as client:
            client.delete(f"{NLP_PIPELINE_URL}/nlp/vectors/{job_id}")
    except Exception as e:
        logger.warning("Vector cleanup failed", extra={"job_id": job_id, "error": str(e)})
        raise self.retry(exc=e, countdown=10)
