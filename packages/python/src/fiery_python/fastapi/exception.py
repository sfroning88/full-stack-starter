"""
Author: Sean Froning
Created Date: 8.17.2026
App Exception handling for FastAPI App
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sentry_sdk import capture_exception
from ..core import logging
from .error import error

logger = logging.get_logger(__name__)


class _Exception:
    """Basic exception handlers"""

    @staticmethod
    def register_exception_handlers(app: FastAPI) -> None:
        @app.exception_handler(error)
        async def handle_app_error(request: Request, exc: error):
            log_fn = logger.warning
            if exc.status_code >= 500:
                log_fn = logger.error
                capture_exception(exc)
            log_fn(
                "app_error",
                error_type=exc.error_type,
                message=exc.message,
                status_code=exc.status_code,
                endpoint=str(request.url.path),
            )
            payload = {"error": exc.to_dict()}
            return JSONResponse(status_code=exc.status_code, content=payload)


exception = _Exception()
