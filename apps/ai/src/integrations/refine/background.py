"""
Author: Sean Froning
Created Date: 8.28.2026
Background functions for Refine
"""

from fiery_python import logging
from fiery_python import TrainingContract
from .services import RefineShardWriter

logger = logging.get_logger(__name__)


class RefineBackgroundJobs:
    """Operations for background jobs from Refine"""

    @staticmethod
    def background_refine_shards(
        contract: TrainingContract, version_id: str, max_samples: int
    ) -> None:
        """Background: Refine shards from storage"""
        if not contract.id:
            logger.error("contract_missing_id", version_id=version_id)
            raise
        logging.bind_job_context(session_id=contract.id)
        try:
            sample_count = RefineShardWriter.run(contract, version_id, max_samples)
            logger.info(
                "refine_shards_job_completed",
                contract_id=contract.id,
                version_id=version_id,
                deformation_id=contract.deformation_id or "None",
                seismic_id=contract.seismic_id or "None",
                sample_count=sample_count,
            )
        except Exception as err:
            logger.error(
                "refine_shards_job_failed",
                contract_id=contract.id,
                version_id=version_id,
                deformation_id=contract.deformation_id or "None",
                seismic_id=contract.seismic_id or "None",
                error=str(err),
            )
            raise
        finally:
            logging.unbind_job_context()
