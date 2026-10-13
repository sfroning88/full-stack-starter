"""
Author: Sean Froning
Created Date: 10.7.2026
Lifespan events for FastAPI app
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from my_python import db_pool, logging, queue, sa

logger = logging.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup")
    queue.get_connection()

    app.state.db_pool = db_pool
    app.state.queue = queue
    app.state.sa = sa

    yield

    logger.info("Application shutdown")
    db_pool.close()
    queue.close()
    sa.close()
