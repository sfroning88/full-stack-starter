"""
Author: Sean Froning
Created Date: 10.7.2026
Background functions for Backend
"""

from my_python import logging
from .services import PersistService

logger = logging.get_logger(__name__)


class BackgroundJobs:
    """Operations for background jobs"""

    @staticmethod
    def background_job(request_id: str) -> None:
        """Background: (does nothing)"""
        logging.bind_job_context(request_id=request_id)
        try:
            my_class = PersistService.select_last_message()
            if not my_class:
                print("(no message)")
            else:
                print(my_class.message)
            logger.info(
                "backend_message_completed",
                request_id=request_id,
            )
        except Exception as err:
            logger.error(
                "backend_message_job_failed",
                request_id=request_id,
                error=str(err),
            )
            raise
        finally:
            logging.unbind_job_context()
