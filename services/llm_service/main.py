"""
LLM Service — FastAPI entry point.
Requirements: 12.1–12.6, 16.1, 16.3, 16.4
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

from services.llm_service.llm.suggestion_generator import generate_suggestions
from services.llm_service.schemas import SuggestionRequest, SuggestionResult

load_dotenv()


def _configure_logging() -> None:
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(fmt="%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())


_configure_logging()
logger = logging.getLogger("llm_service")

app = FastAPI(title="LLM Service", version="1.0.0")

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
        "response_time_ms": duration_ms, "service": "llm_service",
    })
    response.headers["X-Request-ID"] = request_id
    return response


Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.get("/health", tags=["ops"])
def health() -> dict:
    api_key_set = bool(os.getenv("OPENAI_API_KEY", ""))
    return {
        "status": "ok" if api_key_set else "degraded",
        "service": "llm_service",
        "dependencies": {"openai_api_key": "configured" if api_key_set else "missing"},
    }


@app.post("/llm/suggestions", response_model=SuggestionResult, tags=["llm"])
async def suggestions(body: SuggestionRequest) -> SuggestionResult:
    """Generate resume improvement suggestions. Requirements: 12.1–12.6"""
    ats_result = body.ats_result
    skill_gap = body.ats_result.get("skill_gap", {}) if "skill_gap" in body.ats_result else {}

    # skill_gap may be passed directly in the request body
    if not skill_gap and hasattr(body, "skill_gap"):
        skill_gap = body.skill_gap  # type: ignore[attr-defined]

    return await generate_suggestions(
        ats_score=ats_result.get("score", 0),
        skill_gap=skill_gap,
        section_scores=ats_result.get("section_scores", {}),
        resume_text=body.resume_text,
        jd_text=body.jd_text,
    )
