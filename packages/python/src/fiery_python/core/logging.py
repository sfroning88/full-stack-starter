"""
Author: Sean Froning
Created Date: 8.17.2026
Centralized logging with structlog
"""

import sys
import structlog
from structlog import DropEvent
from typing import Optional, Dict
from ..constants import SENTRY_HEALTH_PATHS, SENTRY_JOB_CONTEXT_TAG_KEYS
from .config import config

LOG_FORMAT = config.get_log_format()


class _Logging:
    """Centralized logging configuration with structlog"""

    def __init__(self) -> None:
        self._configured = False

    def drop_health_logs(self, _logger, _method_name, event_dict):
        path = event_dict.get("path") or event_dict.get("request_path")
        if path in SENTRY_HEALTH_PATHS:
            raise DropEvent
        return event_dict

    def configure_structlog(self) -> None:
        if self._configured:
            return
        shared_processors = [
            structlog.stdlib.filter_by_level,
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            self.drop_health_logs,
        ]
        if LOG_FORMAT == "json":
            renderer = structlog.processors.JSONRenderer()
        else:
            renderer = structlog.dev.ConsoleRenderer(colors=True)
        structlog.configure(
            processors=shared_processors + [renderer],
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        self._configured = True

    def setup_structured_logging(self):
        import logging

        logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.INFO)
        self.configure_structlog()

    def get_logger(self, name: str):
        return structlog.get_logger(name)

    def bind_middleware_context(
        self,
        correlation_id: str,
        path: Optional[str] = None,
    ):
        ctx = {"correlation_id": correlation_id}
        if path is not None:
            ctx["path"] = path
        structlog.contextvars.bind_contextvars(**ctx)

    def bind_job_context(self, **fields: str) -> None:
        ctx: Dict[str, str] = {}
        for key, value in fields.items():
            if key not in SENTRY_JOB_CONTEXT_TAG_KEYS or value is None:
                raise ValueError(
                    f"Unrecognized key/value pair for binding context: {key}"
                )
            ctx[str(key)] = value
        if ctx:
            structlog.contextvars.bind_contextvars(**ctx)

    def clear_context(self):
        structlog.contextvars.clear_contextvars()

    def unbind_job_context(self) -> None:
        structlog.contextvars.unbind_contextvars(*SENTRY_JOB_CONTEXT_TAG_KEYS)


logging = _Logging()
