"""
Author: Sean Froning
Created Date: 8.28.2026
Processing functions for Llaima source
"""

import numpy as np
from datasets import load_dataset
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterator, List, Optional
from fiery_python import config, error
from fiery_python import (
    TRAINING_DB_PAGE_SIZE,
    TrainingSplit,
    TrainingStatus,
    TrainingSampleSource,
    TrainingSeismicLabel,
    DatasetIngest,
    TrainingSeismicEvent,
    BlobStorageServices,
)
from .persist_service import IngestPersistService

HF_TOKEN = config.get("HF_TOKEN")

_HF_ID = "sfroning88/Llaima"
_HF_REVISION = "112a804fff40dda73f20265be67934f5f33b34e5"
_HF_SPLIT_MAP = (
    ("train", TrainingSplit.TRAIN),
    ("validation", TrainingSplit.VALIDATE),
    ("test", TrainingSplit.TEST),
)
_SAMPLING_HZ = 100
_STATION = "LAV"
_RECORDED_EPOCH = datetime(2010, 1, 1, tzinfo=timezone.utc)
_LABEL_NAMES = (
    TrainingSeismicLabel.VT,
    TrainingSeismicLabel.LP,
    TrainingSeismicLabel.TR,
    TrainingSeismicLabel.TC,
)
_LABEL_BY_VALUE = {label.value: label for label in _LABEL_NAMES}


class IngestLlaimaSource:
    """Stream Llaima waveforms to unrefined R2 and catalog seismic events"""

    @classmethod
    def run(cls, ingest_id: str, max_samples: int = 5) -> int:
        """Download dataset, store unrefined samples, upsert seismic_events; return asset_count"""
        if max_samples <= 0:
            raise ValueError("max_samples must be positive")
        started_at = datetime.now(timezone.utc)
        IngestPersistService.upsert_ingest(
            DatasetIngest(
                id=ingest_id,
                source=TrainingSampleSource.LLAIMA,
                asset_count=0,
                status=TrainingStatus.EXECUTING,
                started_at=started_at,
            )
        )
        page: List[TrainingSeismicEvent] = []
        asset_count = 0
        try:
            for sample in cls._iter_samples(max_samples):
                body = IngestPersistService.waveform_npz_bytes(sample["waveform"])
                waveform_path = BlobStorageServices.put_unrefined(
                    TrainingSampleSource.LLAIMA, body
                )
                seismic_event = TrainingSeismicEvent(
                    source=TrainingSampleSource.LLAIMA,
                    split=sample.get("split", TrainingSplit.TRAIN),
                    label=sample.get("label", TrainingSeismicLabel.VT),
                    station=sample.get("station"),
                    recorded_at=sample.get("recorded_at"),
                    duration_s=sample.get("duration_s"),
                    sampling_hz=sample.get("sampling_hz"),
                    waveform_path=waveform_path,
                    spectrogram_path=sample.get("spectrogram_path"),
                )
                page.append(seismic_event)
                asset_count += 1
                if len(page) >= TRAINING_DB_PAGE_SIZE:
                    IngestPersistService.upsert_seismic_events(page)
                    page.clear()
                if asset_count >= max_samples:
                    break
            if page:
                IngestPersistService.upsert_seismic_events(page)
            finished_at = datetime.now(timezone.utc)
            IngestPersistService.upsert_ingest(
                DatasetIngest(
                    id=ingest_id,
                    source=TrainingSampleSource.LLAIMA,
                    asset_count=asset_count,
                    status=TrainingStatus.COMPLETED,
                    started_at=started_at,
                    finished_at=finished_at,
                    error_message=None,
                )
            )
            return asset_count
        except Exception as err:
            finished_at = datetime.now(timezone.utc)
            IngestPersistService.upsert_ingest(
                DatasetIngest(
                    id=ingest_id,
                    source=TrainingSampleSource.LLAIMA,
                    asset_count=asset_count,
                    status=TrainingStatus.FAILED,
                    started_at=started_at,
                    finished_at=finished_at,
                    error_message=str(err),
                )
            )
            raise

    @staticmethod
    def _waveform_from_event(row: Any) -> Optional[np.ndarray]:
        if not isinstance(row, dict):
            return None
        array = np.squeeze(np.asarray(row.get("waveform"), dtype=np.float32))
        if array.ndim != 1 or array.size <= 0:
            return None
        return array

    @staticmethod
    def _label_from_event(row: Any) -> Optional[TrainingSeismicLabel]:
        if not isinstance(row, dict):
            return None
        raw = row.get("label")
        if isinstance(raw, int) and 0 <= raw < len(_LABEL_NAMES):
            return _LABEL_NAMES[raw]
        if isinstance(raw, str):
            return _LABEL_BY_VALUE.get(raw.lower())
        return None

    @staticmethod
    def _recorded_at_from_event(index: int) -> datetime:
        return _RECORDED_EPOCH + timedelta(seconds=index)

    @staticmethod
    def _iter_samples(max_samples: int) -> Iterator[Dict[str, Any]]:
        """Yield unrefined waveform plus catalog fields"""
        if not HF_TOKEN or not isinstance(HF_TOKEN, str):
            raise error("HF_TOKEN not configured")
        remaining = max_samples
        index = 0
        for hf_split, training_split in _HF_SPLIT_MAP:
            if remaining <= 0:
                break
            dataset = load_dataset(
                _HF_ID,
                split=hf_split,
                revision=_HF_REVISION,
                token=HF_TOKEN,
                streaming=True,
            )
            dataset = dataset.take(remaining)
            for row in dataset:
                waveform = IngestLlaimaSource._waveform_from_event(row)
                label = IngestLlaimaSource._label_from_event(row)
                if waveform is None or label is None:
                    continue
                sampling_hz = int(row.get("sampling_hz") or _SAMPLING_HZ)
                yield {
                    "waveform": waveform,
                    "label": label,
                    "split": training_split,
                    "station": row.get("station") or _STATION,
                    "sampling_hz": sampling_hz,
                    "duration_s": len(waveform) / sampling_hz,
                    "recorded_at": IngestLlaimaSource._recorded_at_from_event(index),
                }
                index += 1
                remaining -= 1
                if remaining <= 0:
                    break
