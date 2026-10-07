"""
Author: Sean Froning
Created Date: 8.21.2026
Operations pertaining to Ingest persistence
"""

import io
import numpy as np
from psycopg2.extras import execute_values
from typing import List
from fiery_python import db_pool
from fiery_python import (
    TRAINING_DB_PAGE_SIZE,
    DatasetIngest,
    TrainingInterferogram,
    TrainingDeformationSource,
    TrainingSeismicEvent,
    UuidUtils,
)
from ..queries.upsert_dataset_ingest import QUERY as UPSERT_INGEST
from ..queries.upsert_training_interferograms import (
    QUERY as UPSERT_INTERFEROGRAMS,
    TEMPLATE as UPSERT_INTERFEROGRAMS_TEMPLATE,
)
from ..queries.upsert_training_deformation_sources import (
    QUERY as UPSERT_DEFORMATION_SOURCES,
    TEMPLATE as UPSERT_DEFORMATION_SOURCES_TEMPLATE,
)
from ..queries.upsert_training_seismic_events import (
    QUERY as UPSERT_SEISMIC_EVENTS,
    TEMPLATE as UPSERT_SEISMIC_EVENTS_TEMPLATE,
)


class IngestPersistService:
    """Persist ingest, deformation_source, interferograms, seismic_event; unrefined npz bytes"""

    @staticmethod
    def interferogram_npz_bytes(phase: np.ndarray, coherence: np.ndarray) -> bytes:
        stack = np.stack([phase, coherence], axis=0).astype(np.float32)
        buf = io.BytesIO()
        np.savez_compressed(buf, data=stack)
        return buf.getvalue()

    @staticmethod
    def waveform_npz_bytes(waveform: np.ndarray) -> bytes:
        stack = waveform.astype(np.float32)
        buf = io.BytesIO()
        np.savez_compressed(buf, data=stack)
        return buf.getvalue()

    @staticmethod
    def upsert_ingest(ingest: DatasetIngest) -> None:
        db_pool.run(
            UPSERT_INGEST,
            ingest.prepare_for_storage(include_id=True),
        )

    @staticmethod
    def upsert_deformation_sources(
        deformation_sources: List[TrainingDeformationSource],
    ) -> None:
        insert_values = UuidUtils.dedupe_uuid(
            [
                deformation_source.prepare_for_storage(include_id=True)
                for deformation_source in deformation_sources
            ]
        )
        with db_pool.get_cursor() as cursor:
            execute_values(
                cursor,
                UPSERT_DEFORMATION_SOURCES.as_string(cursor),
                insert_values,
                template=UPSERT_DEFORMATION_SOURCES_TEMPLATE.as_string(cursor),
                page_size=TRAINING_DB_PAGE_SIZE,
            )

    @staticmethod
    def upsert_interferograms(interferograms: List[TrainingInterferogram]) -> None:
        insert_values = UuidUtils.dedupe_uuid(
            [
                interferogram.prepare_for_storage(include_id=True)
                for interferogram in interferograms
            ]
        )
        with db_pool.get_cursor() as cursor:
            execute_values(
                cursor,
                UPSERT_INTERFEROGRAMS.as_string(cursor),
                insert_values,
                template=UPSERT_INTERFEROGRAMS_TEMPLATE.as_string(cursor),
                page_size=TRAINING_DB_PAGE_SIZE,
            )

    @staticmethod
    def upsert_seismic_events(seismic_events: List[TrainingSeismicEvent]) -> None:
        insert_values = UuidUtils.dedupe_uuid(
            [
                seismic_event.prepare_for_storage(include_id=True)
                for seismic_event in seismic_events
            ]
        )
        with db_pool.get_cursor() as cursor:
            execute_values(
                cursor,
                UPSERT_SEISMIC_EVENTS.as_string(cursor),
                insert_values,
                template=UPSERT_SEISMIC_EVENTS_TEMPLATE.as_string(cursor),
                page_size=TRAINING_DB_PAGE_SIZE,
            )

    @staticmethod
    def upsert_okada_page(
        deformation_sources: List[TrainingDeformationSource],
        interferograms: List[TrainingInterferogram],
    ) -> None:
        source_values = UuidUtils.dedupe_uuid(
            [
                deformation_source.prepare_for_storage(include_id=True)
                for deformation_source in deformation_sources
            ]
        )
        interferogram_values = UuidUtils.dedupe_uuid(
            [
                interferogram.prepare_for_storage(include_id=True)
                for interferogram in interferograms
            ]
        )
        with db_pool.get_cursor() as cursor:
            execute_values(
                cursor,
                UPSERT_DEFORMATION_SOURCES.as_string(cursor),
                source_values,
                template=UPSERT_DEFORMATION_SOURCES_TEMPLATE.as_string(cursor),
                page_size=TRAINING_DB_PAGE_SIZE,
            )
            execute_values(
                cursor,
                UPSERT_INTERFEROGRAMS.as_string(cursor),
                interferogram_values,
                template=UPSERT_INTERFEROGRAMS_TEMPLATE.as_string(cursor),
                page_size=TRAINING_DB_PAGE_SIZE,
            )
