"""
Author: Sean Froning
Created Date: 10.7.2026
Lifespan events for FastAPI app
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from my_python import (
    db_pool,
    logging,
    queue,
    sa,
    supabase_s3,
    r2_s3,
)

logger = logging.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup")
    queue.get_connection()

    app.state.db_pool = db_pool
    app.state.queue = queue
    app.state.sa = sa
    app.state.supabase_s3 = supabase_s3
    app.state.r2_s3 = r2_s3

    yield

    logger.info("Application shutdown")
    db_pool.close()
    queue.close()
    sa.close()
    supabase_s3.close()
    r2_s3.close()
