"""
Author: Sean Froning
Created Date: 8.28.2026
Processing functions for Refine manifest
"""

from typing import Any, Dict, Optional, Union, assert_never
from fiery_python import (
    Shard,
    TrainingDeformation,
    TrainingDeformationLabel,
    TrainingSeismic,
    TrainingSeismicLabel,
    TrainingSplit,
)

_Label = Union[TrainingDeformationLabel, TrainingSeismicLabel]
_Params = Union[TrainingDeformation, TrainingSeismic]


class RefineShardManifest:
    """Accumulate split counts, class balance, and shard index for a refine job"""

    def __init__(
        self,
        contract_id: str,
        transform_hash: str,
        params: _Params,
    ) -> None:
        self._contract_id = contract_id
        self._transform_hash = transform_hash
        self._params = params
        if isinstance(params, TrainingDeformation):
            labels = TrainingDeformationLabel
        elif isinstance(params, TrainingSeismic):
            labels = TrainingSeismicLabel
        else:
            assert_never(params)
        self._splits: Dict[str, Dict[str, Any]] = {
            split.value: {
                "sample_count": 0,
                "rejected_count": 0,
                "label_counts": {label.value: 0 for label in labels},
                "rejected_label_counts": {label.value: 0 for label in labels},
                "shards": [],
            }
            for split in TrainingSplit
        }

    def record_kept(self, split: TrainingSplit, label: _Label) -> None:
        bucket = self._splits[split.value]
        bucket["sample_count"] += 1
        bucket["label_counts"][label.value] += 1

    def record_reject(
        self,
        split: TrainingSplit,
        label: Optional[_Label],
        reason: str,
    ) -> None:
        bucket = self._splits[split.value]
        bucket["rejected_count"] += 1
        if label is not None:
            bucket["rejected_label_counts"][label.value] += 1
        reasons = bucket.setdefault("reject_reasons", {})
        reasons[reason] = reasons.get(reason, 0) + 1

    def record_shard(
        self,
        split: TrainingSplit,
        key: str,
        sample_count: int,
        nbytes: int,
    ) -> None:
        self._splits[split.value]["shards"].append(
            {
                "key": key,
                "sample_count": sample_count,
                "bytes": nbytes,
            }
        )

    def sample_count(self) -> int:
        return sum(bucket["sample_count"] for bucket in self._splits.values())

    def rejected_count(self) -> int:
        return sum(bucket["rejected_count"] for bucket in self._splits.values())

    def shard_count(self) -> int:
        return sum(len(bucket["shards"]) for bucket in self._splits.values())

    def payload(self) -> Dict[str, Any]:
        snapshot: Dict[str, Any]
        if isinstance(self._params, TrainingDeformation):
            snapshot = {
                "patch_px": self._params.patch_px,
                "wrap_rad": str(self._params.wrap_rad),
                "normalize": self._params.normalize.value,
                "coherence_min": str(self._params.coherence_min),
            }
        elif isinstance(self._params, TrainingSeismic):
            snapshot = {
                "nfft": self._params.nfft,
                "hop": self._params.hop,
                "window": self._params.window.value,
                "window_s": str(self._params.window_s),
                "sampling_hz": self._params.sampling_hz,
                "mel_bins": self._params.mel_bins,
                "bandpass_low_hz": str(self._params.bandpass_low_hz),
                "bandpass_high_hz": str(self._params.bandpass_high_hz),
                "normalize": self._params.normalize.value,
                "snr_min": str(self._params.snr_min),
            }
        else:
            assert_never(self._params)
        return {
            "format_version": 1,
            "contract_id": self._contract_id,
            "transform_hash": self._transform_hash,
            **snapshot,
            "sample_count": self.sample_count(),
            "rejected_count": self.rejected_count(),
            "shard_count": self.shard_count(),
            "splits": self._splits,
        }

    def dumps(self) -> bytes:
        return Shard.write_manifest(self.payload())
