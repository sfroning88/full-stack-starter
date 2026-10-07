"""
Author: Sean Froning
Created Date: 8.17.2026
Health check for FastAPI App
"""

import atexit
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from fiery_python import db_pool, logging

logger = logging.get_logger(__name__)

router = APIRouter(prefix="", tags=["health"])

CHECK_TIMEOUT = 5
_executor = ThreadPoolExecutor(max_workers=2)
atexit.register(_executor.shutdown, wait=False)


def _check_db() -> bool:
    try:
        db_pool.run("SELECT 1")
        return True
    except Exception as err:
        logger.warning("DB health check failed", error=str(err))
        return False


def _check_redis() -> bool:
    try:
        from core import queue

        conn = queue.get_connection()
        conn.ping()
        return True
    except Exception as err:
        logger.warning("Redis health check failed", error=str(err))
        return False


@router.get("/health")
def liveness():
    return {"status": "ok"}


@router.get("/ready")
def readiness():
    db_ok = redis_ok = False
    try:
        future_db = _executor.submit(_check_db)
        future_redis = _executor.submit(_check_redis)
        db_ok = future_db.result(timeout=CHECK_TIMEOUT)
        redis_ok = future_redis.result(timeout=CHECK_TIMEOUT)
    except TimeoutError:
        logger.warning("Health check timed out")
    if db_ok and redis_ok:
        return {"status": "ok"}
    return JSONResponse(
        status_code=503,
        content={"status": "unavailable", "db": db_ok, "redis": redis_ok},
    )
