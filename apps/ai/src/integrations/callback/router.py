"""
Author: Sean Froning
Created Date: 8.24.2026
Core AI API orchestration
"""

from fastapi import APIRouter, Header, Request
from datetime import datetime, timezone
from typing import List
from fiery_python import (
    error,
    logging,
    limiter,
)
from fiery_python import (
    TrainingStatus,
    ModelArtifact,
    ModelMetric,
    MlflowTrackingServices,
)
from .schemas import CallbackRequest, CallbackResponse

logger = logging.get_logger(__name__)

router = APIRouter(
    prefix="/api",
    responses={404: {"description": "Not found"}},
)


callback_available: bool = False
try:
    from ..train import TrainPersistService
    from .services.persist_service import CallbackPersistService
    from .services.verify_artifact import CallbackVerifyArtifact

    callback_available = True
except ImportError as err:
    callback_available = False
    logger.error("Failed to import Callback", error=str(err))
except Exception as err:
    callback_available = False
    logger.error("Failed to boot up Callback", error=str(err))


@router.post("/callback/train")
@limiter.limit("12/hour")
async def callback_train(
    request: Request,
    payload: CallbackRequest,
    x_callback_hmac: str = Header(default=""),
) -> CallbackResponse:
    """Verify Modal artifact and persist unpromoted model entities"""
    if not callback_available:
        raise error("Callback service unavailable", status_code=503)

    session = None

    try:
        CallbackVerifyArtifact.verify_body_signature(payload, x_callback_hmac)

        session = TrainPersistService.select_session(payload.session_id)
        if not session:
            raise error("Fetch session failed", status_code=404)

        if session.status is TrainingStatus.COMPLETED:
            existing = CallbackPersistService.select_artifact(session.id)
            if not existing:
                raise error("Completed session missing artifact", status_code=500)
            return CallbackResponse(
                artifact_id=existing.id,
                session_id=session.id,
            )

        if session.status is not TrainingStatus.EXECUTING:
            raise error("Training session is not executing", status_code=409)

        CallbackVerifyArtifact.verify_object_metadata(
            payload.storage_path, payload.signature
        )

        signed_at = datetime.now(timezone.utc)
        artifact = ModelArtifact(
            tier=payload.tier,
            role=payload.role,
            stage=session.stage,
            precision=payload.precision,
            architecture=payload.architecture,
            param_count=payload.param_count,
            sparsity=payload.sparsity,
            storage_path=payload.storage_path,
            signature=payload.signature,
            signed_at=signed_at,
            promoted=False,
            promoted_at=None,
            mlflow_run_id=None,
            hf_repo_id=payload.hf_repo_id,
            hf_revision=payload.hf_revision,
            session_id=session.id,
            parent_id=payload.parent_id,
        )
        artifact.id = artifact.deterministic_id()

        metrics: List[ModelMetric] = []
        for metric in payload.metrics:
            metric.artifact_id = artifact.id
            metrics.append(metric)

        try:
            artifact.mlflow_run_id = MlflowTrackingServices.log_finished_run(
                artifact, metrics
            )
        except Exception as err:
            logger.warning(
                "mlflow_log_finished_run_failed",
                session_id=session.id,
                artifact_id=artifact.id,
                error=str(err),
            )

        CallbackPersistService.upsert_artifact(artifact)
        CallbackPersistService.upsert_metrics(metrics)

        session.status = TrainingStatus.COMPLETED
        session.finished_at = signed_at
        TrainPersistService.upsert_session(session)

        return CallbackResponse(
            artifact_id=artifact.id,
            session_id=session.id,
        )

    except error:
        raise
    except Exception as err:
        if session is not None:
            session.status = TrainingStatus.FAILED
            session.error_message = str(err)
            TrainPersistService.upsert_session(session)

        logger.error(
            "callback_train_failed",
            session_id=payload.session_id,
            error=str(err),
        )
        raise error("Callback train failed", status_code=500)
