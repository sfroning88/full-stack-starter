"""
Author: Sean Froning
Created Date: 8.22.2026
Unit tests for RefinePersistService
"""

import io
from unittest.mock import patch

import numpy as np
from datetime import datetime, timezone

from fiery_python import (
    TRAINING_DB_FETCH_SIZE,
    DatasetVersion,
    PoolFetch,
    TrainingDeformationLabel,
    TrainingNormalize,
    TrainingSampleSource,
    TrainingSeismicLabel,
    TrainingSignal,
    TrainingSplit,
    TrainingStatus,
    TrainingWindow,
)
from integrations.refine.services.persist_service import RefinePersistService


def test_load_npz_reads_data_key():
    stack = np.stack(
        [np.ones((3, 3), dtype=np.float32), np.full((3, 3), 0.4, dtype=np.float32)]
    )
    buf = io.BytesIO()
    np.savez_compressed(buf, data=stack)
    loaded = RefinePersistService.load_npz(buf.getvalue())
    assert loaded.shape == (2, 3, 3)
    np.testing.assert_array_equal(loaded[0], stack[0])
    np.testing.assert_array_equal(loaded[1], stack[1])


def test_load_npz_reads_waveform_data_key():
    waveform = np.arange(8, dtype=np.float32)
    buf = io.BytesIO()
    np.savez_compressed(buf, data=waveform)
    loaded = RefinePersistService.load_npz(buf.getvalue())
    assert loaded.shape == (8,)
    np.testing.assert_array_equal(loaded, waveform)


def test_select_contract_maps_row():
    row = {
        "signal": TrainingSignal.SEISMIC.value,
        "notes": None,
        "version": 1,
        "seismic_id": "seis-1",
        "deformation_id": None,
    }
    with patch(
        "integrations.refine.services.persist_service.db_pool.run",
        return_value=row,
    ) as run:
        contract = RefinePersistService.select_contract("contract-1")
    run.assert_called_once()
    assert run.call_args.args[1] == ("contract-1",)
    assert run.call_args.kwargs["fetch"] is PoolFetch.ONE
    assert contract.signal is TrainingSignal.SEISMIC
    assert contract.seismic_id == "seis-1"
    assert contract.deformation_id is None


def test_select_contract_returns_none_when_empty():
    with patch(
        "integrations.refine.services.persist_service.db_pool.run",
        return_value=None,
    ):
        assert RefinePersistService.select_contract("contract-1") is None


def test_select_deformation_maps_row():
    row = {
        "id": "def-1",
        "patch_px": 8,
        "wrap_rad": "3.14159",
        "normalize": TrainingNormalize.NONE.value,
        "coherence_min": "0.300",
        "class_id": "class-1",
    }
    with patch(
        "integrations.refine.services.persist_service.db_pool.run",
        return_value=row,
    ) as run:
        deformation = RefinePersistService.select_deformation("contract-1")
    run.assert_called_once()
    assert run.call_args.args[1] == ("contract-1",)
    assert run.call_args.kwargs["fetch"] is PoolFetch.ONE
    assert deformation.id == "def-1"
    assert deformation.patch_px == 8
    assert deformation.normalize is TrainingNormalize.NONE
    assert deformation.class_id == "class-1"


def test_select_deformation_returns_none_when_empty():
    with patch(
        "integrations.refine.services.persist_service.db_pool.run",
        return_value=None,
    ):
        assert RefinePersistService.select_deformation("contract-1") is None


def test_select_seismic_maps_row():
    row = {
        "id": "seis-1",
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
        "class_id": "class-1",
    }
    with patch(
        "integrations.refine.services.persist_service.db_pool.run",
        return_value=row,
    ) as run:
        seismic = RefinePersistService.select_seismic("contract-1")
    run.assert_called_once()
    assert run.call_args.args[1] == ("contract-1",)
    assert run.call_args.kwargs["fetch"] is PoolFetch.ONE
    assert seismic.id == "seis-1"
    assert seismic.nfft == 256
    assert seismic.window is TrainingWindow.HANN
    assert seismic.normalize is TrainingNormalize.NONE
    assert seismic.sampling_hz == 100
    assert seismic.class_id == "class-1"


def test_select_seismic_returns_none_when_empty():
    with patch(
        "integrations.refine.services.persist_service.db_pool.run",
        return_value=None,
    ):
        assert RefinePersistService.select_seismic("contract-1") is None


def test_select_version_maps_row():
    row = {
        "id": "ver-1",
        "transform_hash": "abc",
        "manifest_path": "contract-1/abc/manifest.json",
        "shard_count": 2,
        "sample_count": 10,
        "status": TrainingStatus.COMPLETED.value,
        "contract_id": "other",
    }
    with patch(
        "integrations.refine.services.persist_service.db_pool.run",
        return_value=row,
    ) as run:
        version = RefinePersistService.select_version("contract-1", "abc")
    assert run.call_args.args[1] == ("contract-1", "abc")
    assert version.id == "ver-1"
    assert version.transform_hash == "abc"
    assert version.shard_count == 2
    assert version.status is TrainingStatus.COMPLETED
    assert version.contract_id == "contract-1"


def test_select_version_returns_none_when_empty():
    with patch(
        "integrations.refine.services.persist_service.db_pool.run",
        return_value=None,
    ):
        assert RefinePersistService.select_version("contract-1", "abc") is None


def test_select_interferograms_maps_rows():
    rows = [
        {
            "id": "ifg-1",
            "source": TrainingSampleSource.HEPHAESTUS.value,
            "split": TrainingSplit.TRAIN.value,
            "label": TrainingDeformationLabel.POSITIVE.value,
            "frame_id": "f1",
            "primary_at": None,
            "secondary_at": None,
            "coherence_mean": "0.800",
            "is_augmented": False,
            "storage_path": "hephaestus/abc.npz",
            "deformation_source_id": None,
            "volcano_id": None,
        }
    ]
    with patch(
        "integrations.refine.services.persist_service.db_pool.run",
        return_value=rows,
    ) as run:
        interferograms = RefinePersistService.select_interferograms(
            TrainingSplit.TRAIN,
            "00000000-0000-0000-0000-000000000000",
        )
    assert run.call_args.args[1] == (
        TrainingSplit.TRAIN,
        "00000000-0000-0000-0000-000000000000",
        TRAINING_DB_FETCH_SIZE,
    )
    assert run.call_args.kwargs["fetch"] is PoolFetch.ALL
    assert len(interferograms) == 1
    assert interferograms[0].id == "ifg-1"
    assert interferograms[0].storage_path == "hephaestus/abc.npz"
    assert interferograms[0].label is TrainingDeformationLabel.POSITIVE


def test_select_interferograms_returns_empty_when_missing():
    with patch(
        "integrations.refine.services.persist_service.db_pool.run",
        return_value=None,
    ):
        assert (
            RefinePersistService.select_interferograms(
                TrainingSplit.TEST,
                "00000000-0000-0000-0000-000000000000",
            )
            == []
        )


def test_select_seismic_events_maps_rows():
    recorded_at = datetime(2010, 1, 1, tzinfo=timezone.utc)
    rows = [
        {
            "id": "evt-1",
            "source": TrainingSampleSource.LLAIMA.value,
            "split": TrainingSplit.TRAIN.value,
            "label": TrainingSeismicLabel.LP.value,
            "station": "LAV",
            "recorded_at": recorded_at,
            "duration_s": "60.000",
            "sampling_hz": 100,
            "waveform_path": "llaima/abc.npz",
            "spectrogram_path": None,
            "volcano_id": None,
        }
    ]
    with patch(
        "integrations.refine.services.persist_service.db_pool.run",
        return_value=rows,
    ) as run:
        seismic_events = RefinePersistService.select_seismic_events(
            TrainingSplit.TRAIN,
            "00000000-0000-0000-0000-000000000000",
        )
    assert run.call_args.args[1] == (
        TrainingSplit.TRAIN,
        "00000000-0000-0000-0000-000000000000",
        TRAINING_DB_FETCH_SIZE,
    )
    assert run.call_args.kwargs["fetch"] is PoolFetch.ALL
    assert len(seismic_events) == 1
    assert seismic_events[0].id == "evt-1"
    assert seismic_events[0].waveform_path == "llaima/abc.npz"
    assert seismic_events[0].label is TrainingSeismicLabel.LP
    assert seismic_events[0].station == "LAV"
    assert seismic_events[0].sampling_hz == 100


def test_select_seismic_events_returns_empty_when_missing():
    with patch(
        "integrations.refine.services.persist_service.db_pool.run",
        return_value=None,
    ):
        assert (
            RefinePersistService.select_seismic_events(
                TrainingSplit.TEST,
                "00000000-0000-0000-0000-000000000000",
            )
            == []
        )


def test_upsert_version_passes_storage_dict():
    version = DatasetVersion(
        id="11111111-1111-1111-1111-111111111111",
        transform_hash="abc",
        manifest_path="contract-1/abc/manifest.json",
        shard_count=0,
        sample_count=0,
        status=TrainingStatus.PENDING,
        contract_id="22222222-2222-2222-2222-222222222222",
    )
    with patch("integrations.refine.services.persist_service.db_pool.run") as run:
        RefinePersistService.upsert_version(version)
    run.assert_called_once()
    params = run.call_args.args[1]
    assert params["id"] == version.id
    assert params["transform_hash"] == "abc"
    assert params["status"] == TrainingStatus.PENDING.value
    assert params["contract_id"] == version.contract_id
