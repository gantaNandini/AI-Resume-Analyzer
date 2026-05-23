"""
Shared FastAPI middleware components.

Provides:
- RequestLoggingMiddleware: structured JSON request/response logging
- RequestIdMiddleware: injects X-Request-ID header and sets context var
"""

from __future__ import annotations

import time
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from shared.logging import configure_logging, request_id_var


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware that:
    1. Reads X-Request-ID from incoming request headers (or generates a new UUID).
    2. Sets the request_id context variable for structured logging.
    3. Echoes the request ID back in the X-Request-ID response header.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request_id_var.set(request_id)

        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that emits a structured JSON log entry for every HTTP request,
    including: method, path, status code, and response time in milliseconds.

    Satisfies Requirement 16.1.
    """

    def __init__(self, app, service_name: str = "service") -> None:
        super().__init__(app)
        self.logger = configure_logging(service_name)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        self.logger.info(
            "HTTP request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query": str(request.url.query),
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "client_ip": request.client.host if request.client else "unknown",
            },
        )
        return response
