"""
Scoring Engine service — FastAPI entry point.
Requirements: 9.1–9.5, 10.1–10.5, 11.1–11.5, 14.1–14.5
"""
from __future__ import annotations
import logging
import os
import time
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from pythonjsonlogger import jsonlogger

from services.scoring_engine.cache import get_cached_result, ping as redis_ping, result_hash, set_cached_result
from services.scoring_engine.schemas import ATSResult, ATSScoreRequest, SkillGapRequest, SkillGapResult
from services.scoring_engine.scoring.ats_scorer import classify_score, compute_ats_score
from services.scoring_engine.scoring.formatting_detector import compute_formatting_score
from services.scoring_engine.scoring.hybrid_scorer import compute_hybrid_similarity
from services.scoring_engine.scoring.keyword_density import compute_keyword_density
from services.scoring_engine.scoring.semantic_scorer import compute_cosine_similarity, compute_section_similarities
from services.scoring_engine.scoring.skill_coverage import compute_skill_coverage
from services.scoring_engine.scoring.skill_gap import compute_skill_gap
from services.scoring_engine.scoring.tfidf_scorer import compute_tfidf_score

load_dotenv()


def _configure_logging() -> None:
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(fmt="%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())


_configure_logging()
logger = logging.getLogger("scoring_engine")

app = FastAPI(title="Scoring Engine Service", version="1.0.0")

_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next) -> Response:  # type: ignore[type-arg]
    request_id = str(uuid.uuid4())
    start = time.perf_counter()
    response: Response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info("request", extra={
        "request_id": request_id, "method": request.method,
        "endpoint": str(request.url.path), "status_code": response.status_code,
        "response_time_ms": duration_ms, "service": "scoring_engine",
    })
    response.headers["X-Request-ID"] = request_id
    return response


Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.get("/health", tags=["ops"])
def health() -> dict:
    redis_ok = redis_ping()
    return {
        "status": "ok" if redis_ok else "degraded",
        "service": "scoring_engine",
        "dependencies": {"redis": "ok" if redis_ok else "error"},
    }


@app.post("/scoring/ats-score", tags=["scoring"])
def ats_score(body: ATSScoreRequest, request: Request) -> Response:
    """
    Compute ATS score with Redis cache-aside.
    Returns X-Cache: HIT or MISS header.
    Requirements: 10.1–10.5, 14.1–14.4
    """
    from fastapi.responses import JSONResponse

    cache_key = result_hash(body.resume_text, body.jd_text)
    cached = get_cached_result(cache_key)
    if cached:
        return JSONResponse(content=cached, headers={"X-Cache": "HIT"})

    # Compute scores
    semantic = compute_cosine_similarity(body.resume_embedding, body.jd_embedding)
    tfidf = compute_tfidf_score(body.resume_tokens, body.jd_tokens)
    hybrid = compute_hybrid_similarity(semantic, tfidf)
    keyword_density = compute_keyword_density(body.resume_tokens, body.jd_tokens)
    skill_coverage = compute_skill_coverage(body.resume_skills, body.jd_skills)
    formatting = compute_formatting_score(body.resume_text)
    section_scores = compute_section_similarities(body.resume_section_embeddings, body.jd_section_embeddings)

    score = compute_ats_score(hybrid, keyword_density, skill_coverage, formatting)
    band = classify_score(score)

    result = {
        "score": score,
        "band": band,
        "hybrid_similarity": round(hybrid, 4),
        "section_scores": {k: round(v, 4) for k, v in section_scores.items()},
        "keyword_density": round(keyword_density, 4),
        "skill_coverage": round(skill_coverage, 4),
        "semantic_score": round(semantic, 4),
        "tfidf_score": round(tfidf, 4),
    }

    set_cached_result(cache_key, result)
    return JSONResponse(content=result, headers={"X-Cache": "MISS"})


@app.post("/scoring/skill-gap", tags=["scoring"])
def skill_gap(body: SkillGapRequest) -> dict:
    """Compute skill gap between resume and JD. Requirements: 11.1–11.5"""
    return compute_skill_gap(body.resume_skills, body.jd_skills)
