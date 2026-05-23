"""
File_Processor service — FastAPI entry point.
Requirements: 4.1–4.6, 16.1, 16.3, 16.4
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

from services.file_processor.database import check_db_connection
from services.file_processor.routers.files import router as files_router

load_dotenv()


def _configure_logging() -> None:
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(fmt="%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())


_configure_logging()
logger = logging.getLogger("file_processor")

app = FastAPI(title="File Processor Service", version="1.0.0")

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
        "response_time_ms": duration_ms, "service": "file_processor",
    })
    response.headers["X-Request-ID"] = request_id
    return response


app.include_router(files_router)
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.get("/health", tags=["ops"])
def health() -> dict:
    db_ok = check_db_connection()
    return {"status": "ok" if db_ok else "degraded", "service": "file_processor",
            "dependencies": {"postgres": "ok" if db_ok else "error"}}
