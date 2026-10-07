"""
Author: Sean Froning
Created Date: 8.21.2026
Processing functions for Hephaestus source
"""

import io
import torch
import numpy as np
from datasets import load_dataset
from datetime import datetime, timezone, date
from typing import Any, Dict, Iterator, List, Optional, Tuple
from fiery_python import config, error
from fiery_python import (
    TRAINING_DB_PAGE_SIZE,
    TrainingSplit,
    TrainingStatus,
    TrainingSampleSource,
    TrainingDeformationLabel,
    DatasetIngest,
    TrainingInterferogram,
    BlobStorageServices,
)
from .persist_service import IngestPersistService

HF_TOKEN = config.get("HF_TOKEN")

_HF_ID = "orion-ai-lab/Thalia"
_HF_REVISION = "543216fef7483825e786b3da96caeb1ee197befc"
_HF_SPLIT_MAP = (
    ("train", TrainingSplit.TRAIN),
    ("validation", TrainingSplit.VALIDATE),
    ("test", TrainingSplit.TEST),
)
_PHASE_BAND = 0
_COHERENCE_BAND = 1
_IMAGE_KEYS = ("image.pth", "image")
_SAMPLE_KEYS = ("sample.pth", "sample")


class IngestHephaestusSource:
    """Stream Hephaestus frames to unrefined R2 and catalog interferograms"""

    @classmethod
    def run(cls, ingest_id: str, max_samples: int = 5) -> int:
        """Download pathes, store unrefined samples, upsert interferograms; return asset_count"""
        if max_samples <= 0:
            raise ValueError("max_samples must be positive")
        started_at = datetime.now(timezone.utc)
        IngestPersistService.upsert_ingest(
            DatasetIngest(
                id=ingest_id,
                source=TrainingSampleSource.HEPHAESTUS,
                asset_count=0,
                status=TrainingStatus.EXECUTING,
                started_at=started_at,
            )
        )
        page: List[TrainingInterferogram] = []
        asset_count = 0
        try:
            for sample in cls._iter_samples(max_samples):
                body = IngestPersistService.interferogram_npz_bytes(
                    sample["phase"], sample["coherence"]
                )
                storage_path = BlobStorageServices.put_unrefined(
                    TrainingSampleSource.HEPHAESTUS, body
                )
                interferogram = TrainingInterferogram(
                    source=TrainingSampleSource.HEPHAESTUS,
                    split=sample.get("split", TrainingSplit.TRAIN),
                    label=sample.get("label", TrainingDeformationLabel.NEGATIVE),
                    frame_id=sample.get("frame_id"),
                    primary_at=sample.get("primary_at"),
                    secondary_at=sample.get("secondary_at"),
                    coherence_mean=sample.get("coherence_mean"),
                    storage_path=storage_path,
                )
                page.append(interferogram)
                asset_count += 1
                if len(page) >= TRAINING_DB_PAGE_SIZE:
                    IngestPersistService.upsert_interferograms(page)
                    page.clear()
                if asset_count >= max_samples:
                    break
            if page:
                IngestPersistService.upsert_interferograms(page)
            finished_at = datetime.now(timezone.utc)
            IngestPersistService.upsert_ingest(
                DatasetIngest(
                    id=ingest_id,
                    source=TrainingSampleSource.HEPHAESTUS,
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
                    source=TrainingSampleSource.HEPHAESTUS,
                    asset_count=asset_count,
                    status=TrainingStatus.FAILED,
                    started_at=started_at,
                    finished_at=finished_at,
                    error_message=str(err),
                )
            )
            raise

    @staticmethod
    def _load_pth(value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, dict) or hasattr(value, "shape"):
            return value
        if isinstance(value, (bytes, bytearray, memoryview)):
            return torch.load(
                io.BytesIO(bytes(value)), map_location="cpu", weights_only=True
            )
        return value

    @staticmethod
    def _member(sample: Dict[str, Any], names: Tuple[str, ...]) -> Any:
        for name in names:
            if name in sample and sample[name] is not None:
                return IngestHephaestusSource._load_pth(sample[name])
        return None

    @staticmethod
    def _annotation(sample: Any) -> Dict[str, Any]:
        if not isinstance(sample, dict):
            return {}
        payload = IngestHephaestusSource._member(sample, _SAMPLE_KEYS)
        if isinstance(payload, dict):
            annotations = payload.get("annotation") or []
            if annotations and isinstance(annotations[0], dict):
                return annotations[0]
            return payload
        if isinstance(sample.get("json"), dict):
            return sample["json"]
        return sample

    @staticmethod
    def _parse_yyyymmdd(raw: Any) -> Optional[date]:
        text = str(raw or "")
        if len(text) != 8 or not text.isdigit():
            return None
        return date(int(text[:4]), int(text[4:6]), int(text[6:8]))

    @staticmethod
    def _channels_from_interferogram(
        sample: Any,
    ) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        if not isinstance(sample, dict):
            return None
        cube = IngestHephaestusSource._member(sample, _IMAGE_KEYS)
        if cube is None:
            return None
        array = np.asarray(cube, dtype=np.float32)
        array = np.squeeze(array)
        if array.ndim != 3 or array.shape[0] <= max(_PHASE_BAND, _COHERENCE_BAND):
            return None
        phase: Optional[np.ndarray] = array[_PHASE_BAND]
        coherence: Optional[np.ndarray] = array[_COHERENCE_BAND]
        if phase is None or coherence is None:
            return None
        if phase.shape != coherence.shape:
            return None
        if float(np.nanmax(coherence)) > 1.0:
            coherence = coherence / 255.0
        return phase, np.clip(coherence, 0.0, 1.0)

    @staticmethod
    def _label_interferogram(sample: Any) -> Optional[TrainingDeformationLabel]:
        flags = IngestHephaestusSource._annotation(sample)
        raw = flags.get("label") or []
        if isinstance(raw, str):
            raw = [raw]
        names = {str(item) for item in raw if not isinstance(item, int)}
        if flags.get("corrupted") or flags.get("no_info") or flags.get("low_coherence"):
            return None
        if "Earthquake" in names:
            return TrainingDeformationLabel.UNCERTAIN
        if "Deformation" in names:
            return TrainingDeformationLabel.POSITIVE
        if "Non_Deformation" in names:
            return TrainingDeformationLabel.NEGATIVE
        return TrainingDeformationLabel.UNCERTAIN

    @staticmethod
    def _iter_samples(max_samples: int) -> Iterator[Dict[str, Any]]:
        """Yield unrefined phase/coherence plus catalog fields"""
        if not HF_TOKEN or not isinstance(HF_TOKEN, str):
            raise error("HF_TOKEN not configured")
        remaining = max_samples
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
            for sample in dataset:
                channels = IngestHephaestusSource._channels_from_interferogram(sample)
                if channels is None:
                    continue
                phase, coherence = channels
                flags = IngestHephaestusSource._annotation(sample)
                label = IngestHephaestusSource._label_interferogram(sample)
                if label is None:
                    continue
                yield {
                    "phase": phase,
                    "coherence": coherence,
                    "split": training_split,
                    "label": label,
                    "frame_id": flags.get("frameID") or flags.get("frame_id"),
                    "primary_at": IngestHephaestusSource._parse_yyyymmdd(
                        flags.get("primary_date")
                    ),
                    "secondary_at": IngestHephaestusSource._parse_yyyymmdd(
                        flags.get("secondary_date")
                    ),
                    "coherence_mean": float(np.mean(coherence)),
                }
                remaining -= 1
                if remaining <= 0:
                    break
