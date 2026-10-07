"""
Author: Sean Froning
Created Date: 8.28.2026
Operations pertaining to Refine persistence
"""

import io
import numpy as np
from typing import List, Optional
from fiery_python import db_pool, logging
from fiery_python import (
    TRAINING_DB_FETCH_SIZE,
    PoolFetch,
    DatasetVersion,
    TrainingSplit,
    TrainingInterferogram,
    TrainingSeismicEvent,
    TrainingDeformation,
    TrainingSeismic,
    TrainingContract,
)
from ..queries.select_training_contract import QUERY as SELECT_CONTRACT
from ..queries.select_training_deformation import QUERY as SELECT_DEFORMATION
from ..queries.select_training_seismic import QUERY as SELECT_SEISMIC
from ..queries.select_dataset_version import QUERY as SELECT_VERSION
from ..queries.select_training_interferograms import QUERY as SELECT_INTERFEROGRAMS
from ..queries.select_training_seismic_events import QUERY as SELECT_SEISMIC_EVENTS
from ..queries.upsert_dataset_version import QUERY as UPSERT_VERSION

logger = logging.get_logger(__name__)


class RefinePersistService:
    """Persist version; select version, interferograms, deformation; load npz"""

    @staticmethod
    def load_npz(body: bytes) -> np.ndarray:
        buf = io.BytesIO(body)
        return np.load(buf)["data"]

    @staticmethod
    def select_contract(contract_id: str) -> Optional[TrainingContract]:
        row = db_pool.run(
            SELECT_CONTRACT,
            (contract_id,),
            fetch=PoolFetch.ONE,
            error_event="fetch_training_contract_failed",
        )
        if not row:
            logger.warning("fetch_training_contract_empty", contract_id=contract_id)
            return None
        return TrainingContract(
            id=row.get("id"),
            signal=row.get("signal"),
            notes=row.get("notes"),
            version=row.get("version"),
            seismic_id=row.get("seismic_id"),
            deformation_id=row.get("deformation_id"),
        )

    @staticmethod
    def select_deformation(contract_id: str) -> Optional[TrainingDeformation]:
        row = db_pool.run(
            SELECT_DEFORMATION,
            (contract_id,),
            fetch=PoolFetch.ONE,
            error_event="fetch_training_deformation_failed",
        )
        if not row:
            logger.warning("fetch_training_deformation_empty", contract_id=contract_id)
            return None
        return TrainingDeformation(
            id=row.get("id"),
            patch_px=row.get("patch_px"),
            wrap_rad=row.get("wrap_rad"),
            normalize=row.get("normalize"),
            coherence_min=row.get("coherence_min"),
            class_id=row.get("class_id"),
        )

    @staticmethod
    def select_seismic(contract_id: str) -> Optional[TrainingSeismic]:
        row = db_pool.run(
            SELECT_SEISMIC,
            (contract_id,),
            fetch=PoolFetch.ONE,
            error_event="fetch_training_seismic_failed",
        )
        if not row:
            logger.warning("fetch_training_seismic_empty", contract_id=contract_id)
            return None
        return TrainingSeismic(
            id=row.get("id"),
            nfft=row.get("nfft"),
            hop=row.get("hop"),
            window=row.get("window"),
            window_s=row.get("window_s"),
            sampling_hz=row.get("sampling_hz"),
            mel_bins=row.get("mel_bins"),
            bandpass_low_hz=row.get("bandpass_low_hz"),
            bandpass_high_hz=row.get("bandpass_high_hz"),
            normalize=row.get("normalize"),
            snr_min=row.get("snr_min"),
            class_id=row.get("class_id"),
        )

    @staticmethod
    def select_version(
        contract_id: str, transform_hash: str
    ) -> Optional[DatasetVersion]:
        row = db_pool.run(
            SELECT_VERSION,
            (contract_id, transform_hash),
            fetch=PoolFetch.ONE,
            error_event="fetch_dataset_version_failed",
        )
        if not row:
            logger.warning("fetch_dataset_version_empty", contract_id=contract_id)
            return None
        return DatasetVersion(
            id=row.get("id"),
            transform_hash=row.get("transform_hash"),
            manifest_path=row.get("manifest_path"),
            shard_count=row.get("shard_count"),
            sample_count=row.get("sample_count"),
            status=row.get("status"),
            contract_id=contract_id,
        )

    @staticmethod
    def select_interferograms(
        split: TrainingSplit, after_id: str, limit: int = TRAINING_DB_FETCH_SIZE
    ) -> List[TrainingInterferogram]:
        rows = db_pool.run(
            SELECT_INTERFEROGRAMS,
            (split, after_id, limit),
            fetch=PoolFetch.ALL,
            error_event="fetch_training_interferograms_failed",
        )
        if not rows:
            logger.warning("fetch_training_interferograms_empty")
            return []
        interferograms: List[TrainingInterferogram] = []
        for row in rows:
            interferograms.append(
                TrainingInterferogram(
                    id=row.get("id"),
                    source=row.get("source"),
                    split=row.get("split"),
                    label=row.get("label"),
                    frame_id=row.get("frame_id"),
                    primary_at=row.get("primary_at"),
                    secondary_at=row.get("secondary_at"),
                    coherence_mean=row.get("coherence_mean"),
                    is_augmented=row.get("is_augmented"),
                    storage_path=row.get("storage_path"),
                    deformation_source_id=row.get("deformation_source_id"),
                    volcano_id=row.get("volcano_id"),
                )
            )
        return interferograms

    @staticmethod
    def select_seismic_events(
        split: TrainingSplit, after_id: str, limit: int = TRAINING_DB_FETCH_SIZE
    ) -> List[TrainingSeismicEvent]:
        rows = db_pool.run(
            SELECT_SEISMIC_EVENTS,
            (split, after_id, limit),
            fetch=PoolFetch.ALL,
            error_event="fetch_training_seismic_events_failed",
        )
        if not rows:
            logger.warning("fetch_training_seismic_events_empty")
            return []
        seismic_events: List[TrainingSeismicEvent] = []
        for row in rows:
            seismic_events.append(
                TrainingSeismicEvent(
                    id=row.get("id"),
                    source=row.get("source"),
                    split=row.get("split"),
                    label=row.get("label"),
                    station=row.get("station"),
                    recorded_at=row.get("recorded_at"),
                    duration_s=row.get("duration_s"),
                    sampling_hz=row.get("sampling_hz"),
                    waveform_path=row.get("waveform_path"),
                    spectrogram_path=row.get("spectrogram_path"),
                    volcano_id=row.get("volcano_id"),
                )
            )
        return seismic_events

    @staticmethod
    def upsert_version(version: DatasetVersion) -> None:
        db_pool.run(
            UPSERT_VERSION,
            version.prepare_for_storage(include_id=True),
        )
