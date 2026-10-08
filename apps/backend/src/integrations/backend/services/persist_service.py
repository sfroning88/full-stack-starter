"""
Author: Sean Froning
Created Date: 10.7.2026
Operations pertaining to Backend persistence
"""

from typing import Optional
from my_python import db_pool, logging
from my_python import (
    PoolFetch,
    MyClass,
)
from ..queries.select_last_message import QUERY as SELECT_LAST_MESSAGE

logger = logging.get_logger(__name__)


class PersistService:
    """Print last message"""

    @staticmethod
    def select_last_message() -> Optional[MyClass]:
        row = db_pool.run(
            SELECT_LAST_MESSAGE,
            (),
            fetch=PoolFetch.ONE,
            error_event="fetch_last_message_failed",
        )
        if not row:
            logger.warning("fetch_last_message_empty")
            return None
        return MyClass(
            id=row.get("id"),
            message=row.get("message"),
        )
