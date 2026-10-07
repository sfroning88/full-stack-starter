"""
Author: Sean Froning
Created Date: 8.21.2026
Core AI API orchestration
"""

from uuid import uuid4
from fastapi import APIRouter, Depends, Request
from fiery_python import (
    db_pool,
    dependency,
    error,
    logging,
    queue,
    limiter,
)
from fiery_python import DatasetIngest, TrainingStatus
from .schemas import IngestRequest, IngestResponse
from .queries.upsert_dataset_ingest import QUERY as UPSERT_INGEST

logger = logging.get_logger(__name__)

router = APIRouter(
    prefix="/api",
    responses={404: {"description": "Not found"}},
)


ingest_available: bool = False
try:
    from .background import IngestBackgroundJobs

    ingest_available = True
except ImportError as err:
    ingest_available = False
    logger.error("Failed to import Ingest", error=str(err))
except Exception as err:
    ingest_available = False
    logger.error("Failed to boot up Ingest", error=str(err))


@router.post("/ingest", dependencies=[Depends(dependency.get_token_header)])
@limiter.limit("3/hour")
async def ingest_source(request: Request, payload: IngestRequest) -> IngestResponse:
    """Ingest dataset source"""
    if not ingest_available:
        raise error("Ingest service unavailable", status_code=503)

    ingest_id = str(uuid4())

    try:
        ingest = DatasetIngest(
            id=ingest_id,
            source=payload.source,
            status=TrainingStatus.PENDING,
        )
        db_pool.run(
            UPSERT_INGEST,
            ingest.prepare_for_storage(include_id=True),
        )

        specs = [
            {
                "func": IngestBackgroundJobs.background_ingest_source,
                "args": (payload.source, ingest.id, payload.max_samples),
                "job_id": f"ingest_source_{payload.source.value}_{ingest.id}",
                "job_timeout": 21600,
            }
        ]
        jobs = queue.enqueue_jobs(specs)
        return IngestResponse(job_ids=[job.id for job in jobs])

    except Exception as err:
        ingest = DatasetIngest(
            id=ingest_id,
            source=payload.source,
            status=TrainingStatus.PENDING,
        )
        db_pool.run(UPSERT_INGEST, ingest.prepare_for_storage(include_id=True))

        logger.error(
            "ingest_source_enqueue_failed",
            source=payload.source.value,
            ingest_id=ingest.id,
            error=str(err),
        )
        raise error("Ingest source failed", status_code=500)
