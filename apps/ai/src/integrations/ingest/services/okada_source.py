"""
Author: Sean Froning
Created Date: 8.21.2026
Processing functions for Okada synthetic source
"""

import numpy as np
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Iterator, List, Tuple
from fiery_python import (
    TRAINING_DB_PAGE_SIZE,
    TrainingSplit,
    TrainingStatus,
    TrainingSampleSource,
    TrainingDeformationLabel,
    TrainingDeformationSourceType,
    TrainingNoiseModel,
    DatasetIngest,
    TrainingInterferogram,
    TrainingDeformationSource,
    BlobStorageServices,
)
from .persist_service import IngestPersistService

_PATCH_PX = 128
_WAVELENGTH_M = Decimal("0.0555")
_LOS_INCIDENCE_DEG = Decimal("37.0")
_LOS_HEADING_DEG = Decimal("-10.0")


class IngestOkadaSource:
    """Synthesize Okada-like patches to unrefined R2 and catalog interferograms"""

    @classmethod
    def run(cls, ingest_id: str, max_samples: int = 5) -> int:
        """Augment interferograms; return asset_count"""
        if max_samples <= 0:
            raise ValueError("max_samples must be positive")
        started_at = datetime.now(timezone.utc)
        IngestPersistService.upsert_ingest(
            DatasetIngest(
                id=ingest_id,
                source=TrainingSampleSource.OKADA,
                asset_count=0,
                status=TrainingStatus.EXECUTING,
                started_at=started_at,
            )
        )
        source_page: List[TrainingDeformationSource] = []
        interferogram_page: List[TrainingInterferogram] = []
        asset_count = 0
        try:
            for sample in cls._iter_samples(max_samples):
                deformation_source: TrainingDeformationSource = sample["source"]
                body = IngestPersistService.interferogram_npz_bytes(
                    sample["phase"], sample["coherence"]
                )
                storage_path = BlobStorageServices.put_unrefined(
                    TrainingSampleSource.OKADA, body
                )
                interferogram = TrainingInterferogram(
                    source=TrainingSampleSource.OKADA,
                    split=TrainingSplit.TRAIN,
                    label=sample["label"],
                    coherence_mean=sample["coherence_mean"],
                    storage_path=storage_path,
                    deformation_source_id=deformation_source.id,
                )
                source_page.append(deformation_source)
                interferogram_page.append(interferogram)
                asset_count += 1
                if len(interferogram_page) >= TRAINING_DB_PAGE_SIZE:
                    IngestPersistService.upsert_okada_page(
                        source_page, interferogram_page
                    )
                    source_page.clear()
                    interferogram_page.clear()
                if asset_count >= max_samples:
                    break
            if interferogram_page:
                IngestPersistService.upsert_okada_page(source_page, interferogram_page)
            finished_at = datetime.now(timezone.utc)
            IngestPersistService.upsert_ingest(
                DatasetIngest(
                    id=ingest_id,
                    source=TrainingSampleSource.OKADA,
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
                    source=TrainingSampleSource.OKADA,
                    asset_count=asset_count,
                    status=TrainingStatus.FAILED,
                    started_at=started_at,
                    finished_at=finished_at,
                    error_message=str(err),
                )
            )
            raise

    @staticmethod
    def _forward_phase(slip_m: float) -> Tuple[np.ndarray, np.ndarray]:
        axis = np.linspace(-1.0, 1.0, _PATCH_PX, dtype=np.float32)
        yy, xx = np.meshgrid(axis, axis, indexing="ij")
        envelope = np.exp(-(xx * xx + yy * yy) / (2.0 * 0.18 * 0.18))
        los_m = slip_m * envelope
        wrap = np.pi
        phase = (
            np.mod(los_m * (4.0 * np.pi / float(_WAVELENGTH_M)) + wrap, 2.0 * wrap)
            - wrap
        )
        coherence = np.full((_PATCH_PX, _PATCH_PX), 0.85, dtype=np.float32)
        return phase.astype(np.float32), coherence

    @staticmethod
    def _iter_samples(max_samples: int) -> Iterator[Dict]:
        for index in range(max_samples):
            slip_m = 0.0 if index % 5 == 0 else 0.4 + 0.05 * index
            source = TrainingDeformationSource(
                source=TrainingDeformationSourceType.OKADA,
                latitude=Decimal("-38.0") + Decimal(index) * Decimal("0.01"),
                longitude=Decimal("-71.0"),
                depth_km=Decimal("5.0") + Decimal(index) * Decimal("0.1"),
                strike_deg=Decimal("15.0"),
                dip_deg=Decimal("45.0"),
                rake_deg=Decimal("90.0"),
                slip_m=Decimal(str(slip_m)),
                length_km=Decimal("8.0"),
                width_km=Decimal("6.0"),
                los_incidence_deg=_LOS_INCIDENCE_DEG,
                los_heading_deg=_LOS_HEADING_DEG,
                wavelength_m=_WAVELENGTH_M,
                noise_model=TrainingNoiseModel.NONE,
            )
            source.id = source.deterministic_id()
            phase, coherence = IngestOkadaSource._forward_phase(float(slip_m))
            yield {
                "source": source,
                "phase": phase,
                "coherence": coherence,
                "label": (
                    TrainingDeformationLabel.NEGATIVE
                    if slip_m == 0.0
                    else TrainingDeformationLabel.POSITIVE
                ),
                "coherence_mean": float(np.mean(coherence)),
            }
