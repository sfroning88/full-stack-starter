"""
Author: Sean Froning
Created Date: 10.7.2026
Lifespan events for FastAPI app
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from my_python import db_pool, logging, queue

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
    db_pool.close()
