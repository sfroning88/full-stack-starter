"""
Author: Sean Froning
Created Date: 10.7.2026
Centralized SQL alchemy session
"""

from contextlib import contextmanager
from typing import Iterator, Tuple
from urllib.parse import parse_qs, urlencode, urlparse
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool
from ..resources import SyncLazyResource
from .config import config
from .logging import logging

logger = logging.get_logger(__name__)


class _SqlAlchemy:

    def __init__(self) -> None:
        self._engine = SyncLazyResource(self._init_engine)
        self._sessions = SyncLazyResource(self._init_sessions)

    def _clean_pool_url(self, url: str) -> Tuple[str, bool]:
        """Clean pool url and pgbouncer params"""
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        pooled = "pgbouncer" in qs or parsed.port == 6543
        qs.pop("pgbouncer", None)
        new_q = urlencode(qs, doseq=True)
        cleaned_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        cleaned_params = f"?{new_q}" if new_q else ""
        return cleaned_url + cleaned_params, pooled

    def _init_engine(self) -> Engine:
        """Build engine once on first access"""
        url = config.get_required("database")
        dsn, pooled = self._clean_pool_url(url)
        engine = create_engine(
            dsn,
            poolclass=NullPool if pooled else None,
            pool_pre_ping=True,
        )
        logger.info("SQLAlchemy engine initialized", pooled=pooled)
        return engine

    def _init_sessions(self) -> sessionmaker[Session]:
        """Build session factory once on first access"""
        return sessionmaker(bind=self._engine.get(), expire_on_commit=False)

    @contextmanager
    def get_session(self) -> Iterator[Session]:
        """Get a session that commits, or rolls back on error"""
        session = self._sessions.get()()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self) -> None:
        """Close the engine"""
        self._sessions.pop()
        engine = self._engine.pop()
        if engine is not None:
            engine.dispose()
            logger.info("SQLAlchemy engine closed")

    def reset(self) -> None:
        """Drop the cached engine for forked children to rebuild"""
        self.close()


sa = _SqlAlchemy()
