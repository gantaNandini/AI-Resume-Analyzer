"""
Auth_Service — FastAPI application entry point.

Exposes:
  POST /auth/register  — user registration
  POST /auth/login     — user login
  GET  /health         — liveness + dependency check
  GET  /metrics        — Prometheus metrics

Requirements: 1.1, 2.1, 16.1, 16.3, 16.4
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

from services.auth_service.database import check_db_connection
from services.auth_service.routers.auth import router as auth_router

load_dotenv()

# ---------------------------------------------------------------------------
# Structured JSON logging
# ---------------------------------------------------------------------------

def _configure_logging() -> None:
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())


_configure_logging()
logger = logging.getLogger("auth_service")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Auth Service",
    description="User registration, login, and JWT issuance for the Resume Intelligence Platform.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

_origins = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request logging middleware
# ---------------------------------------------------------------------------

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next) -> Response:  # type: ignore[type-arg]
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start = time.perf_counter()

    response: Response = await call_next(request)

    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        "request",
        extra={
            "request_id": request_id,
            "method": request.method,
            "endpoint": str(request.url.path),
            "status_code": response.status_code,
            "response_time_ms": duration_ms,
            "service": "auth_service",
        },
    )
    response.headers["X-Request-ID"] = request_id
    return response

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(auth_router)

# ---------------------------------------------------------------------------
# Prometheus metrics
# ---------------------------------------------------------------------------

Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------

@app.get("/health", tags=["ops"], summary="Service health check")
def health() -> dict:
    db_ok = check_db_connection()
    return {
        "status": "ok" if db_ok else "degraded",
        "service": "auth_service",
        "dependencies": {
            "postgres": "ok" if db_ok else "error",
        },
    }
