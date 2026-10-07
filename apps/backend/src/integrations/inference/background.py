"""
Author: Sean Froning
Created Date: 8.29.2026
Background functions for Inference
"""

from fiery_python import logging
from fiery_python import ModelTier, ModelRole
from .schemas import InferenceSingleRequest
from .services import InferenceServingOrchestrator

logger = logging.get_logger(__name__)


class InferenceBackgroundJobs:
    """Operations for background jobs from Inference"""

    @staticmethod
    def background_make_inference(
        volcano_id: str, tier: ModelTier, role: ModelRole
    ) -> None:
        """Background: Inference from volcano_id"""
        logging.bind_job_context(volcano_id=volcano_id)
        try:
            payload = InferenceSingleRequest(
                tier=tier,
                role=role,
                volcano_id=volcano_id,
            )
            response = InferenceServingOrchestrator.run(payload)
            logger.info(
                "inference_job_completed",
                volcano_id=volcano_id,
                artifact_id=response.artifact_id,
                transform_hash=response.transform_hash,
            )
        except Exception as err:
            logger.error(
                "inference_job_failed",
                volcano_id=volcano_id,
                error=str(err),
            )
            raise
        finally:
            logging.unbind_job_context()
