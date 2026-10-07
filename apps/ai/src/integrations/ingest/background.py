"""
Author: Sean Froning
Created Date: 8.21.2026
Background functions for Ingest
"""

from fiery_python import logging
from fiery_python import TrainingSampleSource
from .services import (
    IngestHephaestusSource,
    IngestLlaimaSource,
    IngestOkadaSource,
)

logger = logging.get_logger(__name__)


class IngestBackgroundJobs:
    """Operations for background jobs from Ingest"""

    @staticmethod
    def background_ingest_source(
        source: TrainingSampleSource, ingest_id: str, max_samples: int
    ) -> None:
        """Background: Ingest dataset from source"""
        logging.bind_job_context(session_id=ingest_id)
        try:
            match source:
                case TrainingSampleSource.HEPHAESTUS:
                    asset_count = IngestHephaestusSource.run(ingest_id, max_samples)
                case TrainingSampleSource.LLAIMA:
                    asset_count = IngestLlaimaSource.run(ingest_id, max_samples)
                case TrainingSampleSource.OKADA:
                    asset_count = IngestOkadaSource.run(ingest_id, max_samples)
                case _:
                    raise ValueError("unsupported ingest source")
            logger.info(
                "ingest_source_job_completed",
                source=source.value,
                ingest_id=ingest_id,
                asset_count=asset_count,
            )
        except Exception as err:
            logger.error(
                "ingest_source_job_failed",
                source=source.value,
                ingest_id=ingest_id,
                error=str(err),
            )
            raise
        finally:
            logging.unbind_job_context()
