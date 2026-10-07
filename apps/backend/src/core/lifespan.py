"""
Author: Sean Froning
Created Date: 8.17.2026
Lifespan events for FastAPI app
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fiery_python import db_pool, logging, models_s3, queue, r2_s3
from fiery_python import MODEL_REGISTRY_SLOTS
from ml import model_registry

logger = logging.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup")
    queue.get_connection()
    with ThreadPoolExecutor(max_workers=len(MODEL_REGISTRY_SLOTS)) as executor:
        futures = {
            executor.submit(model_registry.load, key): key
            for key in MODEL_REGISTRY_SLOTS
        }
        for future in as_completed(futures):
            key = futures[future]
            try:
                future.result()
            except Exception as err:
                logger.warning(
                    "warmup_skipped",
                    key=key,
                    error=str(err),
                )
    app.state.db_pool = db_pool
    app.state.queue = queue
    app.state.model_registry = model_registry

    yield

    logger.info("Application shutdown")
    queue.close()
    models_s3.close()
    r2_s3.close()
    db_pool.close()
