"""
Author: Sean Froning
Created Date: 8.23.2026
Core AI API orchestration
"""

from fastapi import APIRouter, Depends, Request
from fiery_python import (
    config,
    dependency,
    error,
    logging,
    queue,
    limiter,
)
from fiery_python import (
    TrainingSignal,
    TrainingStatus,
    TrainingSession,
)
from .schemas import TrainRequest, TrainResponse

logger = logging.get_logger(__name__)

router = APIRouter(
    prefix="/api",
    responses={404: {"description": "Not found"}},
)


train_available: bool = False
try:
    from .background import TrainBackgroundJobs
    from .services import TrainPersistService

    train_available = True
except ImportError as err:
    train_available = False
    logger.error("Failed to import Train", error=str(err))
except Exception as err:
    train_available = False
    logger.error("Failed to boot up Train", error=str(err))


_TRAINING_SEED = 42


@router.post("/train", dependencies=[Depends(dependency.get_token_header)])
@limiter.limit("3/hour")
async def train_spawn(request: Request, payload: TrainRequest) -> TrainResponse:
    """Spawn modal training job"""
    if not train_available:
        raise error("Train service unavailable", status_code=503)

    session = None

    try:
        contract = TrainPersistService.select_contract(payload.contract_id)
        if not contract or not contract.id:
            logger.error(
                "fetch_contract_failed",
                contract_id=payload.contract_id,
                version_id=payload.version_id,
            )
            raise error("Fetch contract failed", status_code=500)

        version = TrainPersistService.select_version(payload.version_id)
        if not version or version.contract_id != payload.contract_id:
            logger.error(
                "fetch_version_failed",
                contract_id=payload.contract_id,
                version_id=payload.version_id,
                stage=payload.stage.value,
            )
            raise error("Fetch version failed", status_code=500)

        if version.status is not TrainingStatus.COMPLETED or version.sample_count <= 0:
            raise error("Dataset version is not ready", status_code=400)

        render_commit = config.get("RENDER_GIT_COMMIT")
        git_sha = str(render_commit) if render_commit else None

        if contract.deformation_id:
            signal = TrainingSignal.DEFORMATION

        elif contract.seismic_id:
            signal = TrainingSignal.SEISMIC

        else:
            logger.error(
                "contract_missing_deformation_and_seismic",
                status_code=500,
            )
            raise error("Contract malformed", status_code=500)

        session = TrainingSession(
            signal=signal,
            stage=payload.stage,
            status=TrainingStatus.PENDING,
            samples=version.sample_count,
            seed=_TRAINING_SEED,
            git_sha=git_sha,
            contract_id=payload.contract_id,
            version_id=payload.version_id,
        )

        session.id = session.deterministic_id()

        cached_session = TrainPersistService.select_session(session.id)
        if cached_session and cached_session.status is TrainingStatus.COMPLETED:
            return TrainResponse(
                job_ids=[],
                session_id=cached_session.id,
                cached=True,
            )
        if cached_session and cached_session.status in (
            TrainingStatus.PENDING,
            TrainingStatus.EXECUTING,
        ):
            return TrainResponse(
                job_ids=[],
                session_id=cached_session.id,
                cached=False,
            )
        if cached_session and cached_session.status is TrainingStatus.FAILED:
            session = cached_session
            session.status = TrainingStatus.PENDING
            session.error_message = None
            session.git_sha = git_sha

        TrainPersistService.configure_hyperparameters(session, signal)
        TrainPersistService.upsert_session(session)

        specs = [
            {
                "func": TrainBackgroundJobs.background_spawn_training,
                "args": (session.id, payload.parent_id),
                "job_id": f"train_spawn_{payload.version_id}_{session.id}",
                "job_timeout": 7200,
            }
        ]
        jobs = queue.enqueue_jobs(specs)
        return TrainResponse(
            job_ids=[job.id for job in jobs],
            session_id=session.id,
            cached=False,
        )

    except Exception as err:
        if session is not None:
            session.status = TrainingStatus.FAILED
            session.error_message = str(err)
            TrainPersistService.upsert_session(session)

        logger.error(
            "train_spawn_enqueue_failed",
            contract_id=payload.contract_id,
            error=str(err),
        )
        raise error("Train spawn failed", status_code=500)
