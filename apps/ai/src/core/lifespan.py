"""
Author: Sean Froning
Created Date: 8.17.2026
Lifespan events for FastAPI app
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fiery_python import db_pool, logging, models_s3, queue, r2_s3

logger = logging.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup")
    queue.get_connection()
    app.state.db_pool = db_pool
    app.state.queue = queue

    yield

    logger.info("Application shutdown")
    queue.close()
    models_s3.close()
    r2_s3.close()
    db_pool.close()
