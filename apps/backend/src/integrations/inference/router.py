"""
Author: Sean Froning
Created Date: 8.29.2026
Core backend API orchestration
"""

from fastapi import APIRouter, Depends, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response
from fiery_python import dependency, error, queue, logging, limiter
from fiery_python import VOLCANO_DB_FETCH_SIZE, ModelTier, ModelRole
from .schemas import (
    InferencePreviewRequest,
    InferenceSingleRequest,
    InferenceBatchRequest,
    InferenceSingleResponse,
    InferenceBatchResponse,
)

logger = logging.get_logger(__name__)

router = APIRouter(
    prefix="/api",
    responses={404: {"description": "Not found"}},
)


inference_available: bool = False
try:
    from .services import InferenceImageLoader
    from .services import InferenceServingOrchestrator
    from .services import InferencePersistService
    from .background import InferenceBackgroundJobs

    inference_available = True
except ImportError as err:
    inference_available = False
    logger.error("Failed to import Inference", error=str(err))
except Exception as err:
    inference_available = False
    logger.error("Failed to boot up Inferences", error=str(err))


@router.post("/preview", dependencies=[Depends(dependency.get_token_header)])
@limiter.limit("3/minute")
async def image_preview(request: Request, payload: InferencePreviewRequest) -> Response:
    """Stream interferogram, waveform, or spectogram (if available)"""
    if not inference_available:
        raise error("Inferences service unavailable", status_code=503)

    if not payload.validate_payload():
        raise error("Payload is malformed", status_code=400)

    logging.bind_job_context(
        volcano_id=(payload.interferogram_id or payload.seismic_event_id)
    )
    try:
        return await run_in_threadpool(InferenceImageLoader.run, payload)
    except error:
        raise
    except RuntimeError as err:
        logger.error("image_preview_unavailable", error=str(err))
        raise error(str(err), status_code=503)
    except Exception as err:
        logger.error("image_preview_failed", error=str(err))
        raise error("Image preview failed", status_code=500)
    finally:
        logging.unbind_job_context()


@router.post("/inference/single", dependencies=[Depends(dependency.get_token_header)])
@limiter.limit("3/minute")
async def single_inference(
    request: Request, payload: InferenceSingleRequest
) -> InferenceSingleResponse:
    """Retrieve inference from the promoted model (if available)"""
    if not inference_available:
        raise error("Inferences service unavailable", status_code=503)

    if not payload.validate_payload():
        raise error("Payload is malformed", status_code=400)

    logging.bind_job_context(
        volcano_id=(
            payload.volcano_id or payload.interferogram_id or payload.seismic_event_id
        )
    )
    try:
        return await run_in_threadpool(InferenceServingOrchestrator.run, payload)
    except error:
        raise
    except NotImplementedError:
        logger.warning("model_inference_unsupported")
        raise error("(CLOUD, SCREENER) / (CLOUD, TEACHER) / (EDGE, STUDENT)")
    except ValueError as err:
        logger.warning("model_inference_rejected", error=str(err))
        raise error(str(err), status_code=404)
    except RuntimeError as err:
        logger.error("model_inference_unavailable", error=str(err))
        raise error(str(err), status_code=503)
    except Exception as err:
        logger.error("model_inference_failed", error=str(err))
        raise error("Model inference failed", status_code=500)
    finally:
        logging.unbind_job_context()


@router.post("/inference/batch", dependencies=[Depends(dependency.get_token_header)])
@limiter.limit("3/hour")
async def batch_inference(
    request: Request, payload: InferenceBatchRequest
) -> InferenceBatchResponse:
    """Retrieve inferences from the promoted model (if available)"""
    if not inference_available:
        raise error("Inferences service unavailable", status_code=503)

    try:
        key = (payload.tier, payload.role)
        if (
            key != (ModelTier.CLOUD, ModelRole.SCREENER)
            and key != (ModelTier.CLOUD, ModelRole.TEACHER)
            and key != (ModelTier.EDGE, ModelRole.STUDENT)
        ):
            raise NotImplementedError

        volcanoes = InferencePersistService.select_volcanoes(VOLCANO_DB_FETCH_SIZE)
        volcano_ids = [volcano.id for volcano in volcanoes if volcano.id]
        if not volcano_ids:
            raise error("No volcano_ids found")

        specs = []
        for volcano_id in volcano_ids:
            data = {
                "func": InferenceBackgroundJobs.background_make_inference,
                "args": (volcano_id, payload.tier, payload.role),
                "job_id": f"inference_{payload.tier.value}_{payload.role.value}_{volcano_id}",
                "job_timeout": 6000,
            }
            specs.append(data)

        jobs = queue.enqueue_jobs(specs)
        return InferenceBatchResponse(job_ids=[job.id for job in jobs])

    except NotImplementedError:
        logger.warning("model_inference_unsupported")
        raise error("(CLOUD, SCREENER) / (CLOUD, TEACHER) / (EDGE, STUDENT)")
    except ValueError as err:
        logger.warning("model_inference_rejected", error=str(err))
        raise error(str(err), status_code=404)
    except RuntimeError as err:
        logger.error("model_inference_unavailable", error=str(err))
        raise error(str(err), status_code=503)
    except Exception as err:
        logger.error("model_inference_failed", error=str(err))
        raise error("Model inference failed", status_code=500)
    finally:
        logging.unbind_job_context()
