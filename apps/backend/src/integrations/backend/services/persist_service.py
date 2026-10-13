"""
Author: Sean Froning
Created Date: 10.7.2026
Operations pertaining to Backend persistence
"""

from typing import Optional
from my_python import db_pool, logging, sa
from my_python import (
    PoolFetch,
    MyClass,
)
from ..queries.select_last_message import (
    QUERY_DB_POOL as SELECT_LAST_MESSAGE_DB_POOL,
    QUERY_SQL_ALCHEMY as SELECT_LAST_MESSAGE_SQL_ALCHEMY,
)

logger = logging.get_logger(__name__)


class PersistService:
    """Print last message"""

    @staticmethod
    def select_last_message_using_db_pool() -> Optional[MyClass]:
        row = db_pool.run(
            SELECT_LAST_MESSAGE_DB_POOL,
            (),
            fetch=PoolFetch.ONE,
            error_event="fetch_last_message_failed",
        )
        if not row:
            logger.warning("fetch_last_message_empty_db_pool")
            return None
        return MyClass(
            id=row.get("id"),
            message=row.get("message"),
        )

    @staticmethod
    def select_last_message_using_sql_alchemy() -> Optional[MyClass]:
        with sa.get_session() as session:
            row = session.execute(SELECT_LAST_MESSAGE_SQL_ALCHEMY).mappings().first()
        if not row:
            logger.warning("fetch_last_message_empty_sql_alchemy")
            return None
        return MyClass(
            id=row.get("id"),
            message=row.get("message"),
        )
