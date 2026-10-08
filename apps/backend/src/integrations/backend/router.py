"""
Author: Sean Froning
Created Date: 10.7.2026
Core backend API orchestration
"""

from uuid import uuid4
from fastapi import APIRouter, Depends, Request
from my_python import dependency, error, queue, logging, limiter
from .schemas import BackendRequest, BackendResponse

logger = logging.get_logger(__name__)

router = APIRouter(
    prefix="/api",
    responses={404: {"description": "Not found"}},
)


backend_available: bool = False
try:
    from .background import BackgroundJobs

    backend_available = True
except ImportError as err:
    backend_available = False
    logger.error("Failed to import Backend", error=str(err))
except Exception as err:
    backend_available = False
    logger.error("Failed to boot up Backend", error=str(err))


@router.post("/message", dependencies=[Depends(dependency.get_token_header)])
@limiter.limit("1/minute")
async def backend_message(
    request: Request, _payload: BackendRequest
) -> BackendResponse:
    """Print last message (if available)"""
    if not backend_available:
        raise error("Backend service unavailable", status_code=503)

    try:
        request_id = str(uuid4().hex).strip()[:8]

        specs = []
        data = {
            "func": BackgroundJobs.background_job,
            "args": (request_id,),
            "job_id": f"backend_message_{request_id}",
            "job_timeout": 6000,
        }
        specs.append(data)

        jobs = queue.enqueue_jobs(specs)
        return BackendResponse(job_ids=[job.id for job in jobs])

    except RuntimeError as err:
        logger.error("backend_unavailable", error=str(err))
        raise error(str(err), status_code=503)
    except Exception as err:
        logger.error("backend_failed", error=str(err))
        raise error("Backend failed", status_code=500)
    finally:
        logging.unbind_job_context()
