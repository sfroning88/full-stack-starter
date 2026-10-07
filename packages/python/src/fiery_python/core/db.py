"""
Author: Sean Froning
Created Date: 8.17.2026
Centralized database connection manager
"""

import re
from contextlib import contextmanager
from functools import lru_cache
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union
from urllib.parse import parse_qs, urlencode, urlparse
import psycopg2.pool
from psycopg2.extras import RealDictCursor
from .config import config
from .logging import logging
from ..enums import PoolFetch
from ..resources import SyncLazyResource

logger = logging.get_logger(__name__)


@lru_cache(maxsize=256)
def _normalize_query(query: str) -> str:
    """Rewrite $1... placeholders to psycopg2 %s (cached per query string)"""
    return re.sub(r"\$\d+", "%s", query)


class _DatabaseConnectionPool:

    def __init__(self) -> None:
        self._pool = SyncLazyResource(self._init_pool)

    def _clean_pool_url(self, url: str) -> str:
        """Clean pool url and pgbouncer params"""
        if "?" in url:
            parsed = urlparse(url)
            qs = parse_qs(parsed.query)
            qs.pop("pgbouncer", None)
            new_q = urlencode(qs, doseq=True)
            cleaned_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            cleaned_params = f"?{new_q}" if new_q else ""
            return cleaned_url + cleaned_params
        return url

    def _init_pool(self) -> psycopg2.pool.ThreadedConnectionPool:
        """Build pool once on first access"""
        pool_min = config.get_db_pool_min()
        pool_max = config.get_db_pool_max()
        if pool_min > pool_max:
            raise ValueError("DB_POOL_MIN cannot exceed DB_POOL_MAX")
        url = config.get_required("database")
        dsn = self._clean_pool_url(url)
        domain = config.get_required("domain")
        app_name = "db-" + domain
        pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=pool_min,
            maxconn=pool_max,
            dsn=dsn,
            application_name=app_name,
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=5,
        )
        logger.info("Database pool initialized", pool_min=pool_min, pool_max=pool_max)
        return pool

    def get_conn(self):
        """Get pool connection"""
        return self._pool.get().getconn()

    def put_conn(self, conn) -> None:
        """Put down pool connection"""
        if not self._pool.is_set:
            conn.close()
            return
        self._pool.get().putconn(conn)

    @contextmanager
    def get_cursor(self, cursor_factory=RealDictCursor) -> Iterator[Any]:
        """Get connection wrapped by cursor"""
        conn = cursor = None
        try:
            conn = self.get_conn()
            cursor = conn.cursor(cursor_factory=cursor_factory)
            yield cursor
            conn.commit()
        except Exception:
            if conn:
                conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.put_conn(conn)

    def run(
        self,
        query: Any,
        params: Optional[Tuple] = None,
        *,
        fetch: PoolFetch = PoolFetch.NONE,
        error_event: Optional[str] = None,
        reraise: bool = True,
    ) -> Union[Dict, List[Dict], str, None]:
        """Render (if composed), execute on one cursor, log + handle errors"""
        prepared = _normalize_query(query) if isinstance(query, str) else query
        try:
            with self.get_cursor() as cursor:
                cursor.execute(prepared, params)
                if fetch is PoolFetch.ONE:
                    row = cursor.fetchone()
                    return dict(row) if row else None
                if fetch is PoolFetch.ALL:
                    return [dict(row) for row in cursor.fetchall()]
                return cursor.statusmessage
        except Exception as err:
            if error_event:
                logger.warning(error_event, error=str(err))
            if reraise:
                raise
            return None

    def close(self) -> None:
        """Close pool connection"""
        pool = self._pool.pop()
        if pool is not None:
            pool.closeall()
            logger.info("Database pool closed")

    def reset(self) -> None:
        """Drop the cached pool for forked children to rebuild"""
        self._pool.reset()


db_pool = _DatabaseConnectionPool()
