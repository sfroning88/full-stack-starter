"""
Author: Sean Froning
Created Date: 8.26.2026
Core backend API orchestration
"""

from fastapi import APIRouter, Depends, Request
from fastapi.concurrency import run_in_threadpool
from fiery_python import dependency, error, logging, limiter
from .schemas import (
    ModelPromoteRequest,
    ModelPromoteResponse,
    ModelRefreshRequest,
    ModelRefreshResponse,
)

logger = logging.get_logger(__name__)

router = APIRouter(
    prefix="/api",
    responses={404: {"description": "Not found"}},
)


models_available: bool = False
try:
    from .evaluate import model_evaluator
    from .registry import model_registry

    models_available = True
except ImportError as err:
    models_available = False
    logger.error("Failed to import Models", error=str(err))
except Exception as err:
    models_available = False
    logger.error("Failed to boot up Models", error=str(err))


@router.post("/ml/promote", dependencies=[Depends(dependency.get_token_header)])
@limiter.limit("6/hour")
async def promote_artifact(
    request: Request, payload: ModelPromoteRequest
) -> ModelPromoteResponse:
    """Promote model artifact"""
    if not models_available:
        raise error("Model registry unavailable", status_code=503)

    try:
        evaluated_models = await run_in_threadpool(model_evaluator.run)

        for model in evaluated_models:
            if model.promoted:
                key = (model.tier, model.role)
                await run_in_threadpool(model_registry.load, key, force=True)
                model.ready = model_registry.is_ready(key)

        return ModelPromoteResponse(evaluated_models=evaluated_models)
    except RuntimeError as err:
        logger.error(
            "model_promotion_unavailable",
            error=str(err),
        )
        raise error(str(err), status_code=503)
    except Exception as err:
        logger.error(
            "model_promotion_failed",
            error=str(err),
        )
        raise error("Model promotion failed", status_code=500)


@router.post("/ml/refresh", dependencies=[Depends(dependency.get_token_header)])
@limiter.limit("6/hour")
async def reload_registry(
    request: Request, payload: ModelRefreshRequest
) -> ModelRefreshResponse:
    """Reload model registry"""
    if not models_available:
        raise error("Model registry unavailable", status_code=503)

    try:
        key = (payload.tier, payload.role)
        await run_in_threadpool(model_registry.load, key)

        return ModelRefreshResponse(
            artifact_id=model_registry.get_metadata(key).get("artifact_id"),
            tier=payload.tier,
            role=payload.role,
            ready=model_registry.is_ready(key),
        )
    except RuntimeError as err:
        logger.error(
            "model_registry_unavailable",
            error=str(err),
        )
        raise error(str(err), status_code=503)
    except Exception as err:
        logger.error(
            "model_registry_failed",
            error=str(err),
        )
        raise error("Model registry failed", status_code=500)
