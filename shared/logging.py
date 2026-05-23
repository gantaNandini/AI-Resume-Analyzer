"""
Shared structured JSON logging utilities.

All services should use this module to configure logging so that
every log entry is emitted as a structured JSON object compatible
with log aggregation systems (e.g., Loki, CloudWatch, Datadog).
"""

import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any

from pythonjsonlogger import jsonlogger

# Context variable for request ID propagation across async tasks
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    """Return the current request ID from context, or generate a new one."""
    rid = request_id_var.get()
    if not rid:
        rid = str(uuid.uuid4())
        request_id_var.set(rid)
    return rid


class RequestIdFilter(logging.Filter):
    """Inject the current request_id into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()  # type: ignore[attr-defined]
        return True


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Extend the default JSON formatter to include:
    - request_id
    - service name
    - log level as a string
    """

    def __init__(self, service_name: str, *args: Any, **kwargs: Any) -> None:
        self.service_name = service_name
        super().__init__(*args, **kwargs)

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record["service"] = self.service_name
        log_record["level"] = record.levelname
        log_record["request_id"] = getattr(record, "request_id", "")
        # Remove redundant fields added by the base formatter
        log_record.pop("levelname", None)


def configure_logging(
    service_name: str,
    level: str = "INFO",
    stream: Any = sys.stdout,
) -> logging.Logger:
    """
    Configure and return a structured JSON logger for the given service.

    Usage:
        from shared.logging import configure_logging
        logger = configure_logging("auth_service")
        logger.info("Server started", extra={"port": 8000})
    """
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(stream)
    formatter = CustomJsonFormatter(
        service_name=service_name,
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())
    logger.addHandler(handler)
    logger.propagate = False

    return logger
