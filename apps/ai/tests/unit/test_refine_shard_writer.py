"""
Author: Sean Froning
Created Date: 8.28.2026
Unit tests for RefineShardWriter
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch

import numpy as np
import pytest
from fiery_python import (
    STORAGE_OP_VERSION,
    DatasetVersion,
    TrainingContract,
    TrainingDeformation,
    TrainingDeformationLabel,
    TrainingInterferogram,
    TrainingNormalize,
    TrainingSampleSource,
    TrainingSeismic,
    TrainingSeismicEvent,
    TrainingSeismicLabel,
    TrainingSignal,
    TrainingSplit,
    TrainingStatus,
    TrainingWindow,
    TransformationRejected,
)
from integrations.refine.services.shard_manifest import RefineShardManifest
from integrations.refine.services.shard_writer import RefineShardWriter, _BASE_ID


def _deformation() -> TrainingDeformation:
    return TrainingDeformation(
        patch_px=2,
        wrap_rad=Decimal("3.141592653589793"),
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


def _interferogram(**overrides) -> TrainingInterferogram:
    payload = {
        "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "source": TrainingSampleSource.HEPHAESTUS,
        "split": TrainingSplit.TRAIN,
        "label": TrainingDeformationLabel.POSITIVE,
        "storage_path": "hephaestus/abc.npz",
    }
    payload.update(overrides)
    return TrainingInterferogram(**payload)


def _seismic_event(**overrides) -> TrainingSeismicEvent:
    payload = {
        "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "source": TrainingSampleSource.LLAIMA,
        "split": TrainingSplit.TRAIN,
        "label": TrainingSeismicLabel.LP,
        "station": "LAV",
        "recorded_at": datetime(2010, 1, 1, tzinfo=timezone.utc),
        "duration_s": Decimal("60"),
        "sampling_hz": 100,
        "waveform_path": "llaima/abc.npz",
    }
    payload.update(overrides)
    return TrainingSeismicEvent(**payload)


def _contract_deformation() -> TrainingContract:
    return TrainingContract(
        id="contract-1",
        signal=TrainingSignal.DEFORMATION,
        deformation_id="deform-1",
    )


def _contract_seismic() -> TrainingContract:
    return TrainingContract(
        id="contract-1",
        signal=TrainingSignal.SEISMIC,
        seismic_id="seismic-1",
    )


def _version() -> DatasetVersion:
    return DatasetVersion(
        id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        transform_hash="hash-1",
        manifest_path="contract-1/hash-1/manifest.json",
        shard_count=0,
        sample_count=0,
        status=TrainingStatus.PENDING,
        contract_id="contract-1",
    )


_DEFORMATION = pytest.param(
    _deformation(),
    _interferogram,
    _contract_deformation(),
    "select_interferograms",
    "select_deformation",
    "transform_hash_deformation",
    "apply_deformation",
    np.ones((2, 2, 2), dtype=np.float32),
    np.ones((2, 2), dtype=np.float32),
    "coherence below min",
    TrainingDeformationLabel.POSITIVE.value,
    {"id": None, "storage_path": ""},
    id="deformation",
)
_SEISMIC = pytest.param(
    _seismic(),
    _seismic_event,
    _contract_seismic(),
    "select_seismic_events",
    "select_seismic",
    "transform_hash_seismic",
    "apply_seismic",
    np.ones(100, dtype=np.float32),
    np.ones((1, 8, 4), dtype=np.float32),
    "snr below min",
    TrainingSeismicLabel.LP.value,
    {"id": None, "waveform_path": ""},
    id="seismic",
)
_CASES = (_DEFORMATION, _SEISMIC)


@pytest.mark.parametrize(
    "params, sample_fn, contract, select_samples, select_params, hash_fn, apply_fn, raw, kept, reject_reason, label_value, missing",
    _CASES,
)
def test_transform_rejects_missing_identity(
    params,
    sample_fn,
    contract,
    select_samples,
    select_params,
    hash_fn,
    apply_fn,
    raw,
    kept,
    reject_reason,
    label_value,
    missing,
):
    manifest = RefineShardManifest("contract-1", "hash-1", params)
    sample = sample_fn(**missing)
    sample.id = None
    result = RefineShardWriter._transform_shard(sample, params, manifest)
    assert result is None
    assert manifest.rejected_count() == 1


@pytest.mark.parametrize(
    "params, sample_fn, contract, select_samples, select_params, hash_fn, apply_fn, raw, kept, reject_reason, label_value, missing",
    _CASES,
)
def test_transform_records_rejected_and_returns_none(
    params,
    sample_fn,
    contract,
    select_samples,
    select_params,
    hash_fn,
    apply_fn,
    raw,
    kept,
    reject_reason,
    label_value,
    missing,
):
    manifest = RefineShardManifest("contract-1", "hash-1", params)
    sample = sample_fn()
    with (
        patch(
            "integrations.refine.services.shard_writer.BlobStorageServices.get_unrefined",
            return_value=b"npz",
        ),
        patch(
            "integrations.refine.services.shard_writer.RefinePersistService.load_npz",
            return_value=raw,
        ),
        patch(
            f"integrations.refine.services.shard_writer.Transformation.{apply_fn}",
            side_effect=TransformationRejected(reject_reason),
        ),
    ):
        result = RefineShardWriter._transform_shard(sample, params, manifest)
    assert result is None
    assert manifest.sample_count() == 0
    assert manifest.rejected_count() == 1


@pytest.mark.parametrize(
    "params, sample_fn, contract, select_samples, select_params, hash_fn, apply_fn, raw, kept, reject_reason, label_value, missing",
    _CASES,
)
def test_transform_keeps_array_and_label(
    params,
    sample_fn,
    contract,
    select_samples,
    select_params,
    hash_fn,
    apply_fn,
    raw,
    kept,
    reject_reason,
    label_value,
    missing,
):
    manifest = RefineShardManifest("contract-1", "hash-1", params)
    sample = sample_fn()
    with (
        patch(
            "integrations.refine.services.shard_writer.BlobStorageServices.get_unrefined",
            return_value=b"npz",
        ),
        patch(
            "integrations.refine.services.shard_writer.RefinePersistService.load_npz",
            return_value=raw,
        ),
        patch(
            f"integrations.refine.services.shard_writer.Transformation.{apply_fn}",
            return_value=kept,
        ),
    ):
        key, out, label = RefineShardWriter._transform_shard(sample, params, manifest)
    assert key == sample.id
    np.testing.assert_array_equal(out, kept)
    assert label == {
        "label": label_value,
        "split": TrainingSplit.TRAIN.value,
        "format_version": 1,
        "op_version": STORAGE_OP_VERSION,
    }
    assert manifest.sample_count() == 1


@pytest.mark.parametrize(
    "params, sample_fn, contract, select_samples, select_params, hash_fn, apply_fn, raw, kept, reject_reason, label_value, missing",
    _CASES,
)
def test_flush_shard_puts_tar_and_records(
    params,
    sample_fn,
    contract,
    select_samples,
    select_params,
    hash_fn,
    apply_fn,
    raw,
    kept,
    reject_reason,
    label_value,
    missing,
):
    manifest = RefineShardManifest("contract-1", "hash-1", params)
    buffer = [
        (
            "k1",
            kept,
            {
                "label": label_value,
                "split": "train",
                "format_version": 1,
                "op_version": STORAGE_OP_VERSION,
            },
        )
    ]
    with (
        patch(
            "integrations.refine.services.shard_writer.Shard.write",
            return_value=b"tar-bytes",
        ) as write,
        patch(
            "integrations.refine.services.shard_writer.BlobStorageServices.put_shard",
            return_value="contract-1/hash-1/train-00000.tar",
        ) as put_shard,
    ):
        RefineShardWriter._flush_shard(
            "contract-1",
            "hash-1",
            TrainingSplit.TRAIN,
            0,
            buffer,
            manifest,
        )
    write.assert_called_once_with(buffer)
    put_shard.assert_called_once_with(
        "contract-1", "hash-1", TrainingSplit.TRAIN, 0, b"tar-bytes"
    )
    assert manifest.shard_count() == 1


@pytest.mark.parametrize(
    "params, sample_fn, contract, select_samples, select_params, hash_fn, apply_fn, raw, kept, reject_reason, label_value, missing",
    _CASES,
)
def test_write_split_flushes_when_target_bytes_hit(
    params,
    sample_fn,
    contract,
    select_samples,
    select_params,
    hash_fn,
    apply_fn,
    raw,
    kept,
    reject_reason,
    label_value,
    missing,
):
    samples = [
        sample_fn(id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1"),
        sample_fn(id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2"),
    ]
    manifest = RefineShardManifest("contract-1", "hash-1", params)
    with (
        patch(
            f"integrations.refine.services.shard_writer.RefinePersistService.{select_samples}",
            side_effect=[samples, []],
        ),
        patch.object(
            RefineShardWriter,
            "_transform_shard",
            side_effect=[
                (samples[0].id, kept, {"label": label_value}),
                (samples[1].id, kept, {"label": label_value}),
            ],
        ),
        patch.object(RefineShardWriter, "_flush_shard") as flush,
        patch("integrations.refine.services.shard_writer._TARGET_SHARD_BYTES", 1),
    ):
        kept_count = RefineShardWriter._write_split(
            "contract-1",
            "hash-1",
            TrainingSplit.TRAIN,
            params,
            manifest,
            max_samples=5,
        )
    assert kept_count == 2
    assert flush.call_count == 2


@pytest.mark.parametrize(
    "params, sample_fn, contract, select_samples, select_params, hash_fn, apply_fn, raw, kept, reject_reason, label_value, missing",
    _CASES,
)
def test_run_upserts_completed_and_returns_count(
    params,
    sample_fn,
    contract,
    select_samples,
    select_params,
    hash_fn,
    apply_fn,
    raw,
    kept,
    reject_reason,
    label_value,
    missing,
):
    version = _version()
    with (
        patch(
            f"integrations.refine.services.shard_writer.RefinePersistService.{select_params}",
            return_value=params,
        ),
        patch(
            f"integrations.refine.services.shard_writer.Transformation.{hash_fn}",
            return_value="hash-1",
        ),
        patch(
            "integrations.refine.services.shard_writer.RefinePersistService.select_version",
            return_value=version,
        ),
        patch(
            "integrations.refine.services.shard_writer.RefinePersistService.upsert_version"
        ) as upsert_version,
        patch.object(RefineShardWriter, "_write_split", return_value=3) as write_split,
        patch(
            "integrations.refine.services.shard_writer.BlobStorageServices.put_manifest",
            return_value="contract-1/hash-1/manifest.json",
        ),
    ):
        count = RefineShardWriter.run(contract, version.id, max_samples=7)
    assert count == 3 * len(TrainingSplit)
    assert write_split.call_args.args[5] == 7
    assert write_split.call_count == len(TrainingSplit)
    assert upsert_version.call_args_list[0].args[0].status is TrainingStatus.EXECUTING
    assert upsert_version.call_args_list[-1].args[0].status is TrainingStatus.COMPLETED
    assert upsert_version.call_args_list[-1].args[0].sample_count == 0


@pytest.mark.parametrize(
    "params, sample_fn, contract, select_samples, select_params, hash_fn, apply_fn, raw, kept, reject_reason, label_value, missing",
    _CASES,
)
def test_run_marks_failed_and_reraises(
    params,
    sample_fn,
    contract,
    select_samples,
    select_params,
    hash_fn,
    apply_fn,
    raw,
    kept,
    reject_reason,
    label_value,
    missing,
):
    version = _version()
    with (
        patch(
            f"integrations.refine.services.shard_writer.RefinePersistService.{select_params}",
            return_value=params,
        ),
        patch(
            f"integrations.refine.services.shard_writer.Transformation.{hash_fn}",
            return_value="hash-1",
        ),
        patch(
            "integrations.refine.services.shard_writer.RefinePersistService.select_version",
            return_value=version,
        ),
        patch(
            "integrations.refine.services.shard_writer.RefinePersistService.upsert_version"
        ) as upsert_version,
        patch.object(
            RefineShardWriter, "_write_split", side_effect=RuntimeError("r2 down")
        ),
    ):
        with pytest.raises(RuntimeError, match="r2 down"):
            RefineShardWriter.run(contract, version.id)
    assert upsert_version.call_args_list[-1].args[0].status is TrainingStatus.FAILED


def test_run_rejects_non_positive_max_samples():
    with pytest.raises(ValueError, match="max_samples must be positive"):
        RefineShardWriter.run(_contract_deformation(), _version().id, max_samples=0)
    with pytest.raises(ValueError, match="max_samples must be positive"):
        RefineShardWriter.run(_contract_deformation(), _version().id, max_samples=-1)


@pytest.mark.parametrize(
    "params, sample_fn, contract, select_samples, select_params, hash_fn, apply_fn, raw, kept, reject_reason, label_value, missing",
    _CASES,
)
def test_write_split_pages_until_empty(
    params,
    sample_fn,
    contract,
    select_samples,
    select_params,
    hash_fn,
    apply_fn,
    raw,
    kept,
    reject_reason,
    label_value,
    missing,
):
    first = sample_fn(id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1")
    second = sample_fn(id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2")

    def _pages(_split, after_id, limit):
        assert limit == 1
        if after_id == _BASE_ID:
            return [first]
        if after_id == first.id:
            return [second]
        return []

    manifest = RefineShardManifest("contract-1", "hash-1", params)
    with (
        patch(
            f"integrations.refine.services.shard_writer.RefinePersistService.{select_samples}",
            side_effect=_pages,
        ) as select,
        patch.object(
            RefineShardWriter,
            "_transform_shard",
            side_effect=[
                (first.id, kept, {"label": label_value}),
                (second.id, kept, {"label": label_value}),
            ],
        ),
        patch.object(RefineShardWriter, "_flush_shard") as flush,
        patch("integrations.refine.services.shard_writer.TRAINING_DB_FETCH_SIZE", 1),
    ):
        kept_count = RefineShardWriter._write_split(
            "contract-1",
            "hash-1",
            TrainingSplit.TRAIN,
            params,
            manifest,
            max_samples=10,
        )
    assert kept_count == 2
    assert select.call_count == 3
    assert flush.call_count == 1
    assert select.call_args_list[0].args[1] == _BASE_ID
    assert select.call_args_list[1].args[1] == first.id
    assert select.call_args_list[2].args[1] == second.id


@pytest.mark.parametrize(
    "params, sample_fn, contract, select_samples, select_params, hash_fn, apply_fn, raw, kept, reject_reason, label_value, missing",
    _CASES,
)
def test_write_split_stops_after_max_samples(
    params,
    sample_fn,
    contract,
    select_samples,
    select_params,
    hash_fn,
    apply_fn,
    raw,
    kept,
    reject_reason,
    label_value,
    missing,
):
    samples = [
        sample_fn(id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1"),
        sample_fn(id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2"),
        sample_fn(id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa3"),
    ]
    manifest = RefineShardManifest("contract-1", "hash-1", params)
    with (
        patch(
            f"integrations.refine.services.shard_writer.RefinePersistService.{select_samples}",
            return_value=samples,
        ) as select,
        patch.object(
            RefineShardWriter,
            "_transform_shard",
            side_effect=[
                (samples[0].id, kept, {"label": label_value}),
                (samples[1].id, kept, {"label": label_value}),
            ],
        ),
        patch.object(RefineShardWriter, "_flush_shard") as flush,
    ):
        kept_count = RefineShardWriter._write_split(
            "contract-1",
            "hash-1",
            TrainingSplit.TRAIN,
            params,
            manifest,
            max_samples=2,
        )
    assert kept_count == 2
    assert select.call_count == 1
    assert select.call_args.args[2] == 2
    assert flush.call_count == 1


@pytest.mark.parametrize(
    "params, sample_fn, contract, select_samples, select_params, hash_fn, apply_fn, raw, kept, reject_reason, label_value, missing",
    _CASES,
)
def test_write_split_counts_rejects_toward_max_samples(
    params,
    sample_fn,
    contract,
    select_samples,
    select_params,
    hash_fn,
    apply_fn,
    raw,
    kept,
    reject_reason,
    label_value,
    missing,
):
    samples = [
        sample_fn(id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1"),
        sample_fn(id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2"),
    ]
    manifest = RefineShardManifest("contract-1", "hash-1", params)
    with (
        patch(
            f"integrations.refine.services.shard_writer.RefinePersistService.{select_samples}",
            return_value=samples,
        ),
        patch.object(
            RefineShardWriter,
            "_transform_shard",
            side_effect=[None, (samples[1].id, kept, {"label": label_value})],
        ),
        patch.object(RefineShardWriter, "_flush_shard") as flush,
    ):
        kept_count = RefineShardWriter._write_split(
            "contract-1",
            "hash-1",
            TrainingSplit.TRAIN,
            params,
            manifest,
            max_samples=1,
        )
    assert kept_count == 0
    assert flush.call_count == 0
