"""
NLP Pipeline service — FastAPI entry point.
Requirements: 6.1–6.5, 7.1–7.5, 8.1–8.5, 15.1–15.5
"""
from __future__ import annotations
import logging
import os
import time
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from pythonjsonlogger import jsonlogger

from services.nlp_pipeline.cache.embedding_cache import (
    content_hash, get_cached_embedding, ping as redis_ping, set_cached_embedding,
)
from services.nlp_pipeline.embeddings.generator import generate_embeddings
from services.nlp_pipeline.nlp.preprocessor import preprocess
from services.nlp_pipeline.schemas import (
    EmbedRequest, EmbeddingResult, PreprocessRequest, SkillExtractRequest, SkillManifest,
)
from services.nlp_pipeline.skills.extractor import extract_skills
from services.nlp_pipeline.vectorstore.qdrant_store import (
    delete_by_job_id, ensure_collection, upsert_embedding,
)

load_dotenv()


def _configure_logging() -> None:
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(fmt="%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())


_configure_logging()
logger = logging.getLogger("nlp_pipeline")

app = FastAPI(title="NLP Pipeline Service", version="1.0.0")

_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def startup() -> None:
    try:
        ensure_collection()
    except Exception as e:
        logger.warning("Qdrant collection setup failed", extra={"error": str(e)})


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next) -> Response:  # type: ignore[type-arg]
    request_id = str(uuid.uuid4())
    start = time.perf_counter()
    response: Response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info("request", extra={
        "request_id": request_id, "method": request.method,
        "endpoint": str(request.url.path), "status_code": response.status_code,
        "response_time_ms": duration_ms, "service": "nlp_pipeline",
    })
    response.headers["X-Request-ID"] = request_id
    return response


Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.get("/health", tags=["ops"])
def health() -> dict:
    qdrant_ok = True
    try:
        ensure_collection()
    except Exception:
        qdrant_ok = False
    redis_ok = redis_ping()
    status = "ok" if (qdrant_ok and redis_ok) else "degraded"
    return {
        "status": status, "service": "nlp_pipeline",
        "dependencies": {"qdrant": "ok" if qdrant_ok else "error", "redis": "ok" if redis_ok else "error"},
    }


@app.post("/nlp/preprocess", tags=["nlp"])
def preprocess_document(body: PreprocessRequest) -> dict:
    """Tokenize, lemmatize, NER, section detection."""
    doc = preprocess(body.text, body.document_type, body.job_id)
    return doc.model_dump()


@app.post("/nlp/extract-skills", tags=["nlp"])
def extract_skills_endpoint(body: SkillExtractRequest) -> dict:
    """Extract canonical skills from a preprocessed document."""
    manifest = extract_skills(body.document, body.document_type)
    return manifest.model_dump()


@app.post("/nlp/embed", tags=["nlp"])
def embed_document(body: EmbedRequest) -> dict:
    """Generate embeddings with Redis cache + Qdrant upsert."""
    key = content_hash(body.text)
    cached = get_cached_embedding(key)
    if cached:
        cached["cache_hit"] = True
        return cached

    # Preprocess first to get sections
    doc = preprocess(body.text, body.doc_type, body.job_id)
    result = generate_embeddings(doc)

    # Cache
    result_dict = result.model_dump()
    set_cached_embedding(key, result_dict)

    # Upsert to Qdrant
    try:
        upsert_embedding(
            job_id=body.job_id,
            doc_type=body.doc_type,
            user_id=body.user_id,
            vector=result.full_document,
            metadata={"model": result.model_name},
        )
    except Exception as e:
        logger.warning("Qdrant upsert failed", extra={"error": str(e)})

    result_dict["cache_hit"] = False
    return result_dict


@app.delete("/nlp/vectors/{job_id}", tags=["nlp"])
def delete_vectors(job_id: str) -> dict:
    """Delete all vectors for a job from Qdrant."""
    try:
        delete_by_job_id(job_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"deleted": True, "job_id": job_id}
