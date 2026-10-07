"""
Author: Sean Froning
Created Date: 8.28.2026
Core AI API orchestration
"""

from fastapi import APIRouter, Depends, Request
from fiery_python import (
    dependency,
    error,
    logging,
    queue,
    limiter,
)
from fiery_python import (
    TrainingStatus,
    DatasetVersion,
    Transformation,
    BlobStorageServices,
)
from .schemas import RefineRequest, RefineResponse

logger = logging.get_logger(__name__)

router = APIRouter(
    prefix="/api",
    responses={404: {"description": "Not found"}},
)


refine_available: bool = False
try:
    from .background import RefineBackgroundJobs
    from .services import RefinePersistService

    refine_available = True
except ImportError as err:
    refine_available = False
    logger.error("Failed to import Refine", error=str(err))
except Exception as err:
    refine_available = False
    logger.error("Failed to boot up Refine", error=str(err))


@router.post("/refine", dependencies=[Depends(dependency.get_token_header)])
@limiter.limit("3/hour")
async def refine_shards(request: Request, payload: RefineRequest) -> RefineResponse:
    """Refine dataset shards"""
    if not refine_available:
        raise error("Refine service unavailable", status_code=503)

    version = None

    try:
        contract = RefinePersistService.select_contract(payload.contract_id)
        if not contract or not contract.id:
            logger.error(
                "fetch_contract_failed",
                contract_id=payload.contract_id,
            )
            raise error("Fetch contract failed", status_code=500)

        if contract.deformation_id:
            deformation = RefinePersistService.select_deformation(contract.id)
            if not deformation:
                logger.error(
                    "fetch_deformation_failed",
                    contract_id=contract.id,
                )
                raise error("Fetch deformation failed", status_code=500)

            transform_hash = Transformation.transform_hash_deformation(deformation)

        elif contract.seismic_id:
            seismic = RefinePersistService.select_seismic(contract.id)
            if not seismic:
                logger.error(
                    "fetch_seismic_failed",
                    contract_id=contract.id,
                )

            transform_hash = Transformation.transform_hash_seismic(seismic)

        else:
            logger.error(
                "contract_missing_deformation_and_seismic",
                status_code=500,
            )
            raise error("Contract malformed", status_code=500)

        version = RefinePersistService.select_version(contract.id, transform_hash)

        if version and version.status is TrainingStatus.COMPLETED:
            return RefineResponse(
                job_ids=[],
                version_id=version.id,
                transform_hash=transform_hash,
                cached=True,
            )

        if version and version.status in (
            TrainingStatus.PENDING,
            TrainingStatus.EXECUTING,
        ):
            return RefineResponse(
                job_ids=[],
                version_id=version.id,
                transform_hash=transform_hash,
                cached=False,
            )

        if not version:
            manifest_path = BlobStorageServices._manifest_key(
                contract.id, transform_hash
            )
            version = DatasetVersion(
                transform_hash=transform_hash,
                manifest_path=manifest_path,
                shard_count=0,
                sample_count=0,
                status=TrainingStatus.PENDING,
                contract_id=contract.id,
            )
            version.id = version.deterministic_id()
            RefinePersistService.upsert_version(version)
        elif version.status is TrainingStatus.FAILED:
            version.status = TrainingStatus.PENDING
            RefinePersistService.upsert_version(version)

        specs = [
            {
                "func": RefineBackgroundJobs.background_refine_shards,
                "args": (contract, version.id, payload.max_samples),
                "job_id": f"refine_shards_{contract.id}_{version.id}",
                "job_timeout": 3600,
            }
        ]
        jobs = queue.enqueue_jobs(specs)
        return RefineResponse(
            job_ids=[job.id for job in jobs],
            version_id=version.id,
            transform_hash=transform_hash,
            cached=False,
        )

    except Exception as err:
        if version is not None:
            version.status = TrainingStatus.FAILED
            RefinePersistService.upsert_version(version)

        logger.error(
            "refine_shards_enqueue_failed",
            contract_id=payload.contract_id,
            error=str(err),
        )
        raise error("Refine shards failed", status_code=500)
