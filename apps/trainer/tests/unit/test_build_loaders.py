"""
Author: Sean Froning
Created Date: 8.29.2026
Unit tests for trainer dataset loaders
"""

import json
from unittest.mock import patch

import numpy as np
import pytest
import torch
from torch.utils.data import DataLoader, TensorDataset
from fiery_python import (
    TrainingDeformationLabel,
    TrainingSeismicLabel,
    TrainingSignal,
    TrainingSplit,
    TrainingStage,
)
from src.build_loaders import (
    _DEFORMATION_BATCH_SIZE,
    _SEISMIC_BATCH_SIZE,
    _SEISMIC_EMPTY,
    _VIT_PX,
    _array_to_tensor,
    _build_lora_loaders,
    _build_quantize_loaders,
    _calibrate_loader,
    _generator,
    _label_to_index,
    _load_split_tensors,
    build_loaders,
)


def _manifest() -> dict:
    return {
        "splits": {
            TrainingSplit.TRAIN.value: {"shards": [{"key": "train-00000.tar"}]},
            TrainingSplit.VALIDATE.value: {"shards": [{"key": "val-00000.tar"}]},
            TrainingSplit.TEST.value: {"shards": []},
            TrainingSplit.HOLDOUT.value: {"shards": []},
        }
    }


def test_build_loaders_raises_when_stage_missing():
    with pytest.raises(RuntimeError, match="Missing stage from spec"):
        build_loaders({"stage": None})


def test_build_loaders_raises_when_stage_invalid():
    with pytest.raises(RuntimeError, match="Invalid stage from spec"):
        build_loaders({"stage": "unknown"})


@pytest.mark.parametrize(
    "stage,builder",
    [
        (TrainingStage.PRETRAIN.value, "_build_pretrain_loaders"),
        (TrainingStage.LORA.value, "_build_lora_loaders"),
        (TrainingStage.DISTILL.value, "_build_distill_loaders"),
        (TrainingStage.PRUNE.value, "_build_prune_loaders"),
        (TrainingStage.QUANTIZE.value, "_build_quantize_loaders"),
    ],
)
def test_build_loaders_dispatches_stage(stage: str, builder: str):
    expected = {"train": object()}
    with patch(f"src.build_loaders.{builder}", return_value=expected) as build:
        result = build_loaders({"stage": stage})
    assert result is expected
    build.assert_called_once_with({"stage": stage})


def test_label_to_index_maps_binary_labels():
    signal = TrainingSignal.DEFORMATION
    assert (
        _label_to_index({"label": TrainingDeformationLabel.POSITIVE.value}, signal) == 1
    )
    assert (
        _label_to_index({"label": TrainingDeformationLabel.NEGATIVE.value}, signal) == 0
    )
    assert (
        _label_to_index({"label": TrainingDeformationLabel.UNCERTAIN.value}, signal)
        is None
    )


def test_label_to_index_maps_seismic_labels():
    signal = TrainingSignal.SEISMIC
    assert _label_to_index({"label": TrainingSeismicLabel.VT.value}, signal) == 0
    assert _label_to_index({"label": TrainingSeismicLabel.LP.value}, signal) == 1
    assert _label_to_index({"label": TrainingSeismicLabel.TR.value}, signal) == 2
    assert _label_to_index({"label": TrainingSeismicLabel.TC.value}, signal) == 3
    assert _label_to_index({"label": "unknown"}, signal) is None


def test_array_to_tensor_repeats_and_resizes_phase():
    phase = np.ones((32, 32), dtype=np.float32)
    tensor = _array_to_tensor(phase, TrainingSignal.DEFORMATION)
    assert tensor.shape == (3, _VIT_PX, _VIT_PX)
    assert torch.allclose(tensor[0], tensor[1])


def test_array_to_tensor_rejects_non_hw_phase():
    with pytest.raises(RuntimeError, match="Expected phase array"):
        _array_to_tensor(
            np.ones((2, 8, 8), dtype=np.float32), TrainingSignal.DEFORMATION
        )


def test_array_to_tensor_keeps_log_mel():
    spec = np.ones((1, 8, 16), dtype=np.float32)
    tensor = _array_to_tensor(spec, TrainingSignal.SEISMIC)
    assert tensor.shape == (1, 8, 16)
    assert tensor.dtype == torch.float32


def test_array_to_tensor_rejects_non_mel():
    with pytest.raises(RuntimeError, match="Expected log-mel array"):
        _array_to_tensor(np.ones((8, 16), dtype=np.float32), TrainingSignal.SEISMIC)


def test_generator_is_seeded():
    assert _generator(7).initial_seed() == 7


def test_load_split_tensors_skips_uncertain_and_missing_keys():
    phase = np.ones((_VIT_PX, _VIT_PX), dtype=np.float32)
    splits = {TrainingSplit.TRAIN.value: {"shards": [{"key": "train-00000.tar"}, {}]}}
    unpacked = [
        ("a", phase, {"label": TrainingDeformationLabel.POSITIVE.value}),
        ("b", phase, {"label": TrainingDeformationLabel.UNCERTAIN.value}),
        ("c", phase, {"label": TrainingDeformationLabel.NEGATIVE.value}),
    ]
    with (
        patch("fiery_python.BlobStorageServices.get_shard", return_value=b"tar"),
        patch("fiery_python.Shard.read", return_value=unpacked),
    ):
        images, targets = _load_split_tensors(
            splits, TrainingSplit.TRAIN, TrainingSignal.DEFORMATION
        )
    assert images.shape == (2, 3, _VIT_PX, _VIT_PX)
    assert targets.tolist() == [1, 0]


def test_load_split_tensors_stacks_seismic():
    spec = np.ones((1, 4, 8), dtype=np.float32)
    splits = {TrainingSplit.TRAIN.value: {"shards": [{"key": "train-00000.tar"}]}}
    unpacked = [
        ("a", spec, {"label": TrainingSeismicLabel.VT.value}),
        ("b", spec, {"label": TrainingSeismicLabel.TC.value}),
    ]
    with (
        patch("fiery_python.BlobStorageServices.get_shard", return_value=b"tar"),
        patch("fiery_python.Shard.read", return_value=unpacked),
    ):
        features, targets = _load_split_tensors(
            splits, TrainingSplit.TRAIN, TrainingSignal.SEISMIC
        )
    assert features.shape == (2, 1, 4, 8)
    assert targets.tolist() == [0, 3]


def test_load_split_tensors_empty_when_no_shards():
    images, targets = _load_split_tensors(
        {}, TrainingSplit.TEST, TrainingSignal.DEFORMATION
    )
    assert images.shape[0] == 0
    assert targets.shape[0] == 0


def test_load_split_tensors_empty_seismic_shape():
    features, targets = _load_split_tensors(
        {}, TrainingSplit.TEST, TrainingSignal.SEISMIC
    )
    assert tuple(features.shape) == _SEISMIC_EMPTY
    assert targets.shape[0] == 0


def test_build_lora_loaders_caps_train_and_skips_empty_splits():
    phase = np.ones((_VIT_PX, _VIT_PX), dtype=np.float32)
    unpacked = [
        ("a", phase, {"label": TrainingDeformationLabel.POSITIVE.value}),
        ("b", phase, {"label": TrainingDeformationLabel.NEGATIVE.value}),
        ("c", phase, {"label": TrainingDeformationLabel.POSITIVE.value}),
    ]
    spec = {
        "manifest_path": "contract/hash/manifest.json",
        "seed": 42,
        "samples": 2,
        "signal": TrainingSignal.DEFORMATION.value,
    }
    with (
        patch(
            "src.build_loaders.r2_s3.get_bytes",
            return_value=json.dumps(_manifest()).encode("utf-8"),
        ),
        patch("fiery_python.BlobStorageServices.get_shard", return_value=b"tar"),
        patch("fiery_python.Shard.read", return_value=unpacked),
    ):
        loaders = _build_lora_loaders(spec)
    assert set(loaders) == {
        TrainingSplit.TRAIN.value,
        TrainingSplit.VALIDATE.value,
    }
    train_images, train_targets = next(iter(loaders[TrainingSplit.TRAIN.value]))
    assert train_images.shape[0] == 2
    assert train_targets.shape[0] == 2
    assert loaders[TrainingSplit.TRAIN.value].batch_size == _DEFORMATION_BATCH_SIZE


def test_build_lora_loaders_raises_when_manifest_missing():
    with pytest.raises(RuntimeError, match="Missing manifest_path from spec"):
        _build_lora_loaders(
            {
                "seed": 1,
                "manifest_path": None,
                "signal": TrainingSignal.DEFORMATION.value,
            }
        )


def test_build_lora_loaders_raises_when_train_empty():
    manifest = {"splits": {TrainingSplit.TRAIN.value: {"shards": []}}}
    with patch(
        "src.build_loaders.r2_s3.get_bytes",
        return_value=json.dumps(manifest).encode("utf-8"),
    ):
        with pytest.raises(RuntimeError, match="Empty train split"):
            _build_lora_loaders(
                {
                    "manifest_path": "contract/hash/manifest.json",
                    "seed": 1,
                    "signal": TrainingSignal.DEFORMATION.value,
                }
            )


def test_build_quantize_loaders_adds_calibrate():
    spec = np.ones((1, 4, 8), dtype=np.float32)
    unpacked = [
        ("a", spec, {"label": TrainingSeismicLabel.VT.value}),
        ("b", spec, {"label": TrainingSeismicLabel.LP.value}),
        ("c", spec, {"label": TrainingSeismicLabel.TR.value}),
    ]
    payload = {
        "manifest_path": "contract/hash/manifest.json",
        "seed": 42,
        "signal": TrainingSignal.SEISMIC.value,
        "quantize": {"calibration_samples": 2},
    }
    with (
        patch(
            "src.build_loaders.r2_s3.get_bytes",
            return_value=json.dumps(_manifest()).encode("utf-8"),
        ),
        patch("fiery_python.BlobStorageServices.get_shard", return_value=b"tar"),
        patch("fiery_python.Shard.read", return_value=unpacked),
    ):
        loaders = _build_quantize_loaders(payload)
    assert "calibrate" in loaders
    assert len(loaders["calibrate"].dataset) == 2
    assert loaders["train"].batch_size == _SEISMIC_BATCH_SIZE


def test_calibrate_loader_is_seeded_subset():
    features = torch.zeros(5, 1, 4, 8)
    targets = torch.arange(5)
    train = DataLoader(TensorDataset(features, targets), batch_size=2)
    first = _calibrate_loader(
        train, {"seed": 7, "quantize": {"calibration_samples": 3}}
    )
    second = _calibrate_loader(
        train, {"seed": 7, "quantize": {"calibration_samples": 3}}
    )
    assert first.dataset.indices == second.dataset.indices
    assert len(first.dataset.indices) == 3
