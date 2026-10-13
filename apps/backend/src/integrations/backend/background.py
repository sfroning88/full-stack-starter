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
            my_class_db_pool = PersistService.select_last_message_using_db_pool()
            my_class_sql_alchemy = (
                PersistService.select_last_message_using_sql_alchemy()
            )
            my_class_db_pool_message = (
                my_class_db_pool.message if my_class_db_pool else "None"
            )
            my_class_sql_alchemy_message = (
                my_class_sql_alchemy.message if my_class_sql_alchemy else "None"
            )
            if not my_class_db_pool and not my_class_sql_alchemy:
                logger.warning("no message", request_id=request_id)
            elif my_class_db_pool_message != my_class_sql_alchemy_message:
                logger.warning(
                    "message mismatch",
                    request_id=request_id,
                    db_pool_message=my_class_db_pool_message,
                    sql_alchemy_message=my_class_sql_alchemy_message,
                )
            else:
                logger.info(
                    "message fetched",
                    request_id=request_id,
                    db_pool_message=my_class_db_pool_message,
                    sql_alchemy_message=my_class_sql_alchemy_message,
                )
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
