"""
Shared structured JSON logging configuration.
Requirements: 16.1, 16.2
"""
from __future__ import annotations
import logging
import os
import time
import uuid

from pythonjsonlogger import jsonlogger


def configure_logging(service_name: str = "service") -> None:
    """Configure structured JSON logging for a service."""
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
    logging.getLogger(service_name).info(
        "Logging configured", extra={"service": service_name}
    )


def make_request_logging_middleware(service_name: str):
    """
    Returns a FastAPI HTTP middleware that logs every request with:
    request_id, method, endpoint, status_code, response_time_ms
    Requirements: 16.1
    """
    from fastapi import Request, Response

    logger = logging.getLogger(service_name)

    async def middleware(request: Request, call_next) -> Response:  # type: ignore[type-arg]
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start = time.perf_counter()
        try:
            response: Response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.error(
                "Unhandled exception",
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "endpoint": str(request.url.path),
                    "response_time_ms": duration_ms,
                    "service": service_name,
                },
            )
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
                headers={"X-Request-ID": request_id},
            )
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "endpoint": str(request.url.path),
                "status_code": response.status_code,
                "response_time_ms": duration_ms,
                "service": service_name,
            },
        )
        response.headers["X-Request-ID"] = request_id
        return response

    return middleware
