"""
Author: Sean Froning
Created Date: 8.17.2026
Middleware protection for FastAPI App
"""

import uuid
import time
import re
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from ..core import logging

logger = logging.get_logger(__name__)
CORRELATION_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


class _Middleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        incoming_correlation_id = request.headers.get("x-correlation-id")
        correlation_id = (
            incoming_correlation_id
            if incoming_correlation_id
            and CORRELATION_ID_RE.fullmatch(incoming_correlation_id)
            else str(uuid.uuid4())
        )
        path = request.url.path
        logging.bind_middleware_context(correlation_id=correlation_id, path=path)
        request.state.correlation_id = correlation_id
        start_time = time.perf_counter()
        logger.info("request_started", method=request.method, path=request.url.path)
        response = None
        try:
            response = await call_next(request)
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            status_code = getattr(response, "status_code", 500) if response else 500
            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                duration_ms=round(duration_ms, 2),
            )
            logging.clear_context()
        if response:
            response.headers["x-correlation-id"] = correlation_id
            response.headers["x-response-time-ms"] = str(round(duration_ms, 2))
        return response


middleware = _Middleware
