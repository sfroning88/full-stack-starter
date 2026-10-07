"""
Author: Sean Froning
Created Date: 8.29.2026
Build training dataset
"""

import numpy as np
from torch import Generator, Tensor
from torch.utils.data import DataLoader, Subset, TensorDataset
from typing import Dict, Optional, Tuple, assert_never
from fiery_python import r2_s3
from fiery_python import (
    TrainingStage,
    TrainingSignal,
    TrainingSplit,
    TrainingDeformationLabel,
    TrainingSeismicLabel,
)

_DEFORMATION_BATCH_SIZE = 16
_SEISMIC_BATCH_SIZE = 32
_VIT_PX = 224
_LABEL_INDEX = {
    TrainingSignal.DEFORMATION: {
        TrainingDeformationLabel.POSITIVE.value: 1,
        TrainingDeformationLabel.NEGATIVE.value: 0,
    },
    TrainingSignal.SEISMIC: {
        TrainingSeismicLabel.VT.value: 0,
        TrainingSeismicLabel.LP.value: 1,
        TrainingSeismicLabel.TR.value: 2,
        TrainingSeismicLabel.TC.value: 3,
    },
}
_DEFORMATION_EMPTY = (0, 3, _VIT_PX, _VIT_PX)
_SEISMIC_EMPTY = (0, 1, 0, 0)


def build_loaders(spec: dict) -> Dict[str, DataLoader]:
    stage = spec["stage"]
    if not stage or not isinstance(stage, str):
        raise RuntimeError("Missing stage from spec")
    match stage:
        case TrainingStage.PRETRAIN.value:
            return _build_pretrain_loaders(spec)
        case TrainingStage.LORA.value:
            return _build_lora_loaders(spec)
        case TrainingStage.DISTILL.value:
            return _build_distill_loaders(spec)
        case TrainingStage.PRUNE.value:
            return _build_prune_loaders(spec)
        case TrainingStage.QUANTIZE.value:
            return _build_quantize_loaders(spec)
        case _:
            raise RuntimeError(f"Invalid stage from spec: {stage}")


def _build_pretrain_loaders(spec: dict) -> Dict[str, DataLoader]:
    return _build_split_loaders(
        spec, batch_size=_nested_int(spec, "pretrain", "batch_size")
    )


def _build_lora_loaders(spec: dict) -> Dict[str, DataLoader]:
    return _build_split_loaders(spec, batch_size=_DEFORMATION_BATCH_SIZE)


def _build_distill_loaders(spec: dict) -> Dict[str, DataLoader]:
    return _build_split_loaders(
        spec, batch_size=_nested_int(spec, "distill", "batch_size")
    )


def _build_prune_loaders(spec: dict) -> Dict[str, DataLoader]:
    return _build_split_loaders(spec, batch_size=_SEISMIC_BATCH_SIZE)


def _build_quantize_loaders(spec: dict) -> Dict[str, DataLoader]:
    loaders = _build_split_loaders(spec, batch_size=_SEISMIC_BATCH_SIZE)
    loaders["calibrate"] = _calibrate_loader(loaders["train"], spec)
    return loaders


def _build_split_loaders(spec: dict, *, batch_size: int) -> Dict[str, DataLoader]:
    splits = _manifest_splits(spec)
    seed = spec["seed"]
    samples = spec.get("samples")
    signal = _signal(spec)
    loaders: Dict[str, DataLoader] = {}
    for split in TrainingSplit:
        features, targets = _load_split_tensors(splits, split, signal)
        if split is TrainingSplit.TRAIN and isinstance(samples, int) and samples > 0:
            features = features[:samples]
            targets = targets[:samples]
        if features.shape[0] == 0:
            if split is TrainingSplit.TRAIN:
                raise RuntimeError("Empty train split")
            continue
        loaders[split.value] = DataLoader(
            TensorDataset(features, targets),
            batch_size=batch_size,
            shuffle=split is TrainingSplit.TRAIN,
            generator=_generator(seed),
            pin_memory=True,
            num_workers=0,
        )
    return loaders


def _manifest_splits(spec: dict) -> dict:
    import json
    from fiery_python import STORAGE_SHARD_BUCKET_NAME

    manifest_path = spec["manifest_path"]
    if not manifest_path or not isinstance(manifest_path, str):
        raise RuntimeError("Missing manifest_path from spec")
    manifest = json.loads(r2_s3.get_bytes(STORAGE_SHARD_BUCKET_NAME, manifest_path))
    return manifest.get("splits") or {}


def _load_split_tensors(
    splits: dict, split: TrainingSplit, signal: TrainingSignal
) -> Tuple[Tensor, Tensor]:
    import torch
    from fiery_python import BlobStorageServices, Shard

    bucket = splits.get(split.value) or {}
    shards = bucket.get("shards") or []
    features = []
    targets = []
    for shard in shards:
        key = shard.get("key")
        if not key:
            continue
        unpacked = Shard.read(BlobStorageServices.get_shard(key))
        for _sample_key, array, label in unpacked:
            target = _label_to_index(label, signal)
            if target is None:
                continue
            features.append(_array_to_tensor(array, signal))
            targets.append(target)
    if not features:
        if signal is TrainingSignal.DEFORMATION:
            empty = _DEFORMATION_EMPTY
        elif signal is TrainingSignal.SEISMIC:
            empty = _SEISMIC_EMPTY
        else:
            assert_never(signal)
        return torch.empty(empty), torch.empty(0, dtype=torch.long)
    return torch.stack(features), torch.tensor(targets, dtype=torch.long)


def _array_to_tensor(array: np.ndarray, signal: TrainingSignal) -> Tensor:
    import torch
    import torch.nn.functional as F

    tensor = torch.from_numpy(np.ascontiguousarray(array)).float()
    if signal is TrainingSignal.DEFORMATION:
        if tensor.ndim != 2:
            raise RuntimeError("Expected phase array of shape (H, W)")
        tensor = tensor.unsqueeze(0).unsqueeze(0)
        if tensor.shape[-2] != _VIT_PX or tensor.shape[-1] != _VIT_PX:
            tensor = F.interpolate(
                tensor, size=(_VIT_PX, _VIT_PX), mode="bilinear", align_corners=False
            )
        return tensor.squeeze(0).repeat(3, 1, 1)
    if signal is TrainingSignal.SEISMIC:
        if tensor.ndim != 3 or tensor.shape[0] != 1:
            raise RuntimeError("Expected log-mel array of shape (1, M, F)")
        return tensor


def _label_to_index(label: dict, signal: TrainingSignal) -> Optional[int]:
    value = label.get("label")
    mapping = _LABEL_INDEX.get(signal)
    if mapping is None:
        return None
    return mapping.get(value)


def _calibrate_loader(train_loader: DataLoader, spec: dict) -> DataLoader:
    import torch

    dataset = train_loader.dataset
    requested = spec.get("quantize") or {}
    num_samples = requested.get("calibration_samples") or 100
    num_samples = min(int(num_samples), len(dataset))
    if num_samples <= 0:
        raise RuntimeError("Empty calibration split")
    generator = _generator(spec["seed"])
    indices = torch.randperm(len(dataset), generator=generator)[:num_samples].tolist()
    return DataLoader(
        Subset(dataset, indices),
        batch_size=train_loader.batch_size,
        shuffle=False,
        pin_memory=True,
        num_workers=0,
    )


def _signal(spec: dict) -> TrainingSignal:
    value = spec.get("signal")
    if value == TrainingSignal.DEFORMATION.value:
        return TrainingSignal.DEFORMATION
    if value == TrainingSignal.SEISMIC.value:
        return TrainingSignal.SEISMIC
    raise RuntimeError("Missing signal from spec")


def _nested_int(spec: dict, block: str, field: str) -> int:
    payload = spec.get(block) or {}
    value = payload.get(field)
    if not isinstance(value, int) or value <= 0:
        raise RuntimeError(f"Missing {block}.{field} from spec")
    return value


def _generator(seed: int) -> Generator:
    import torch

    generator = torch.Generator()
    generator.manual_seed(seed)
    return generator
