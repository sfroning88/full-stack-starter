"""
Author: Sean Froning
Created Date: 8.28.2026
Unit tests for RefineShardManifest
"""

import json
from decimal import Decimal

import pytest
from fiery_python import (
    TrainingDeformation,
    TrainingDeformationLabel,
    TrainingNormalize,
    TrainingSeismic,
    TrainingSeismicLabel,
    TrainingSplit,
    TrainingWindow,
)
from integrations.refine.services.shard_manifest import RefineShardManifest


def _deformation() -> TrainingDeformation:
    return TrainingDeformation(
        patch_px=8,
        wrap_rad=Decimal("3.14159"),
        normalize=TrainingNormalize.NONE,
        coherence_min=Decimal("0.300"),
        class_id="class-1",
    )


def _seismic() -> TrainingSeismic:
    return TrainingSeismic(
        nfft=256,
        hop=128,
        window=TrainingWindow.HANN,
        window_s=Decimal("60"),
        sampling_hz=100,
        mel_bins=64,
        bandpass_low_hz=Decimal("1.00"),
        bandpass_high_hz=Decimal("10.00"),
        normalize=TrainingNormalize.NONE,
        snr_min=Decimal("0.300"),
        class_id="class-1",
    )


_CASES = (
    pytest.param(
        _deformation(),
        {
            "patch_px": 8,
            "wrap_rad": "3.14159",
            "normalize": TrainingNormalize.NONE.value,
            "coherence_min": "0.300",
        },
        TrainingDeformationLabel.POSITIVE,
        TrainingDeformationLabel.NEGATIVE,
        TrainingDeformationLabel.UNCERTAIN,
        "coherence below min",
        id="deformation",
    ),
    pytest.param(
        _seismic(),
        {
            "nfft": 256,
            "hop": 128,
            "window": TrainingWindow.HANN.value,
            "window_s": "60",
            "sampling_hz": 100,
            "mel_bins": 64,
            "bandpass_low_hz": "1.00",
            "bandpass_high_hz": "10.00",
            "normalize": TrainingNormalize.NONE.value,
            "snr_min": "0.300",
        },
        TrainingSeismicLabel.VT,
        TrainingSeismicLabel.LP,
        TrainingSeismicLabel.TR,
        "snr below min",
        id="seismic",
    ),
)


@pytest.mark.parametrize(
    "params, snapshot, kept_a, kept_b, rejected_label, reject_reason",
    _CASES,
)
def test_payload_starts_with_zero_counts(
    params, snapshot, kept_a, kept_b, rejected_label, reject_reason
):
    manifest = RefineShardManifest("contract-1", "hash-1", params)
    payload = manifest.payload()
    assert payload["format_version"] == 1
    assert payload["contract_id"] == "contract-1"
    assert payload["transform_hash"] == "hash-1"
    for key, value in snapshot.items():
        assert payload[key] == value
    assert payload["sample_count"] == 0
    assert payload["rejected_count"] == 0
    assert payload["shard_count"] == 0
    assert set(payload["splits"].keys()) == {split.value for split in TrainingSplit}
    assert payload["splits"]["train"]["label_counts"][kept_a.value] == 0


@pytest.mark.parametrize(
    "params, snapshot, kept_a, kept_b, rejected_label, reject_reason",
    _CASES,
)
def test_record_kept_and_reject_update_totals(
    params, snapshot, kept_a, kept_b, rejected_label, reject_reason
):
    manifest = RefineShardManifest("contract-1", "hash-1", params)
    manifest.record_kept(TrainingSplit.TRAIN, kept_a)
    manifest.record_kept(TrainingSplit.TRAIN, kept_b)
    manifest.record_reject(TrainingSplit.VALIDATE, rejected_label, reject_reason)
    manifest.record_reject(TrainingSplit.VALIDATE, None, "missing_identity")
    assert manifest.sample_count() == 2
    assert manifest.rejected_count() == 2
    train = manifest.payload()["splits"]["train"]
    assert train["sample_count"] == 2
    assert train["label_counts"][kept_a.value] == 1
    assert train["label_counts"][kept_b.value] == 1
    validate = manifest.payload()["splits"]["validate"]
    assert validate["rejected_count"] == 2
    assert validate["rejected_label_counts"][rejected_label.value] == 1
    assert validate["reject_reasons"][reject_reason] == 1
    assert validate["reject_reasons"]["missing_identity"] == 1


@pytest.mark.parametrize(
    "params, snapshot, kept_a, kept_b, rejected_label, reject_reason",
    _CASES,
)
def test_record_shard_indexes_keys(
    params, snapshot, kept_a, kept_b, rejected_label, reject_reason
):
    manifest = RefineShardManifest("contract-1", "hash-1", params)
    manifest.record_shard(
        TrainingSplit.TRAIN, "contract-1/hash-1/train-00000.tar", 4, 128
    )
    manifest.record_shard(TrainingSplit.TEST, "contract-1/hash-1/test-00000.tar", 1, 32)
    assert manifest.shard_count() == 2
    train_shards = manifest.payload()["splits"]["train"]["shards"]
    assert train_shards[0]["key"] == "contract-1/hash-1/train-00000.tar"
    assert train_shards[0]["sample_count"] == 4
    assert train_shards[0]["bytes"] == 128


@pytest.mark.parametrize(
    "params, snapshot, kept_a, kept_b, rejected_label, reject_reason",
    _CASES,
)
def test_dumps_is_canonical_json_bytes(
    params, snapshot, kept_a, kept_b, rejected_label, reject_reason
):
    manifest = RefineShardManifest("contract-1", "hash-1", params)
    manifest.record_kept(TrainingSplit.TRAIN, kept_a)
    body = manifest.dumps()
    restored = json.loads(body)
    assert restored["sample_count"] == 1
    for key, value in snapshot.items():
        assert restored[key] == value
    assert body == json.dumps(restored, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
