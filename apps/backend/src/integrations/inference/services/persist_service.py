"""
Author: Sean Froning
Created Date: 8.29.2026
Operations pertaining to Inference persistence
"""

import io
import numpy as np
from typing import List, Optional, Tuple
from fiery_python import db_pool, logging
from fiery_python import (
    PoolFetch,
    VOLCANO_DB_FETCH_SIZE,
    InferenceDeformation,
    InferenceSeismic,
    TrainingInterferogram,
    TrainingSeismicEvent,
    TrainingDeformation,
    TrainingSeismic,
    Volcano,
)
from ..queries.select_volcanoes import QUERY as SELECT_VOLCANOES
from ..queries.select_training_interferogram import QUERY as SELECT_INTERFEROGRAM
from ..queries.select_training_seismic_event import QUERY as SELECT_SEISMIC_EVENT
from ..queries.select_training_deformation import QUERY as SELECT_DEFORMATION
from ..queries.select_training_seismic import QUERY as SELECT_SEISMIC
from ..queries.upsert_inference_deformation import QUERY as UPSERT_DEFORMATION
from ..queries.upsert_inference_seismic import QUERY as UPSERT_SEISMIC

logger = logging.get_logger(__name__)


class InferencePersistService:
    """Load npz bytes; select interferogram, seismic_event, deformation, seismic; upsert deformation, seismic"""

    @staticmethod
    def load_npz(body: bytes) -> np.ndarray:
        buf = io.BytesIO(body)
        return np.load(buf)["data"]

    @staticmethod
    def select_volcanoes(limit: int = VOLCANO_DB_FETCH_SIZE) -> List[Volcano]:
        rows = db_pool.run(
            SELECT_VOLCANOES,
            (limit,),
            fetch=PoolFetch.ALL,
            error_event="fetch_volcanoes_failed",
        )
        if not rows:
            logger.warning("fetch_volcanoes_empty")
            return []
        volcanoes: List[Volcano] = []
        for row in rows:
            volcanoes.append(
                Volcano(
                    id=row.get("id"),
                    gvp_number=row.get("gvp_number"),
                    name=row.get("name"),
                    country=row.get("country"),
                    zone=row.get("zone"),
                    latitude=row.get("latitude"),
                    longitude=row.get("longitude"),
                    elevation_m=row.get("elevation_m"),
                    volcanic_class=row.get("volcanic_class"),
                    is_glaciated=row.get("is_glaciated"),
                    is_instrumented=row.get("is_instrumented"),
                    is_held_out=row.get("is_held_out"),
                    image_path=row.get("image_path"),
                )
            )
        return volcanoes

    @staticmethod
    def select_interferogram(
        interferogram_or_volcano_id: Tuple[Optional[str], Optional[str]],
    ) -> Optional[TrainingInterferogram]:
        interferogram_id, volcano_id = interferogram_or_volcano_id
        if not interferogram_id and not volcano_id:
            logger.warning("fetch_training_interferogram_impossible")
            return None
        row = db_pool.run(
            SELECT_INTERFEROGRAM,
            (interferogram_id, volcano_id),
            fetch=PoolFetch.ONE,
            error_event="fetch_training_interferogram_failed",
        )
        if not row:
            logger.warning(
                "fetch_training_interferogram_empty",
                interferogram_id=interferogram_id or "None",
                volcano_id=volcano_id or "None",
            )
            return None
        return TrainingInterferogram(
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

    @staticmethod
    def select_seismic_event(
        seismic_event_or_volcano_id: Tuple[Optional[str], Optional[str]],
    ) -> Optional[TrainingSeismicEvent]:
        seismic_event_id, volcano_id = seismic_event_or_volcano_id
        if not seismic_event_id and not volcano_id:
            logger.warning("fetch_training_seismic_event_impossible")
            return None
        row = db_pool.run(
            SELECT_SEISMIC_EVENT,
            (seismic_event_id, volcano_id),
            fetch=PoolFetch.ONE,
            error_event="fetch_training_seismic_event_failed",
        )
        if not row:
            logger.warning(
                "fetch_training_seismic_event_empty",
                interferogram_id=seismic_event_id or "None",
                volcano_id=volcano_id or "None",
            )
            return None
        return TrainingSeismicEvent(
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

    @staticmethod
    def select_deformation(session_id: str) -> Optional[TrainingDeformation]:
        row = db_pool.run(
            SELECT_DEFORMATION,
            (session_id,),
            fetch=PoolFetch.ONE,
            error_event="fetch_training_deformation_failed",
        )
        if not row:
            logger.warning("fetch_training_deformation_empty", session_id=session_id)
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
    def select_seismic(session_id: str) -> Optional[TrainingSeismic]:
        row = db_pool.run(
            SELECT_SEISMIC,
            (session_id,),
            fetch=PoolFetch.ONE,
            error_event="fetch_training_seismic_failed",
        )
        if not row:
            logger.warning("fetch_training_seismic_empty", session_id=session_id)
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
    def upsert_deformation(deformation: InferenceDeformation) -> None:
        db_pool.run(
            UPSERT_DEFORMATION,
            deformation.prepare_for_storage(include_id=False),
        )

    @staticmethod
    def upsert_seismic(seismic: InferenceSeismic) -> None:
        db_pool.run(
            UPSERT_SEISMIC,
            seismic.prepare_for_storage(include_id=False),
        )
