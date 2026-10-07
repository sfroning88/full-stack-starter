"""
Author: Sean Froning
Created Date: 8.28.2026
Background functions for Train
"""

from typing import Optional
from fiery_python import logging
from .services import TrainModalSpawn

logger = logging.get_logger(__name__)


class TrainBackgroundJobs:
    """Operations for background jobs from Train"""

    @staticmethod
    def background_spawn_training(
        session_id: str, parent_id: Optional[str] = None
    ) -> None:
        """Background: Build job spec and spawn training job"""
        logging.bind_job_context(session_id=session_id)
        try:
            call_id = TrainModalSpawn.run(session_id, parent_id)
            logger.info(
                "train_spawn_job_completed",
                session_id=session_id,
                parent_id=parent_id or "None",
                call_id=call_id,
            )
        except Exception as err:
            logger.error(
                "train_spawn_job_failed",
                session_id=session_id,
                parent_id=parent_id or "None",
                error=str(err),
            )
            raise
        finally:
            logging.unbind_job_context()
