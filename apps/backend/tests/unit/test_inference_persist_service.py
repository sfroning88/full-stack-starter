"""
Author: Sean Froning
Created Date: 8.29.2026
Unit tests for InferencePersistService
"""

import io
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch

import numpy as np
from fiery_python import (
    PoolFetch,
    InferenceDeformation,
    InferenceSeismic,
    TrainingDeformationLabel,
    TrainingNormalize,
    TrainingSampleSource,
    TrainingSeismicLabel,
    TrainingSplit,
    TrainingWindow,
    VOLCANO_DB_FETCH_SIZE,
    VolcanoZone,
)
from integrations.inference.services.persist_service import InferencePersistService


def test_load_npz_reads_data_key():
    stack = np.stack(
        [np.ones((3, 3), dtype=np.float32), np.full((3, 3), 0.4, dtype=np.float32)]
    )
    buf = io.BytesIO()
    np.savez_compressed(buf, data=stack)
    loaded = InferencePersistService.load_npz(buf.getvalue())
    assert loaded.shape == (2, 3, 3)
    np.testing.assert_array_equal(loaded[0], stack[0])
    np.testing.assert_array_equal(loaded[1], stack[1])


def test_select_volcanoes_maps_rows():
    rows = [
        {
            "id": "vol-1",
            "gvp_number": 357070,
            "name": "Llaima",
            "country": "Chile",
            "zone": VolcanoZone.SVZ.value,
            "latitude": "-38.692000",
            "longitude": "-71.729000",
            "elevation_m": 3125,
            "volcanic_class": "stratovolcano",
            "is_glaciated": True,
            "is_instrumented": True,
            "is_held_out": True,
            "image_path": None,
        },
        {
            "id": "vol-2",
            "gvp_number": None,
            "name": "Villarrica",
            "country": "Chile",
            "zone": VolcanoZone.SVZ.value,
            "latitude": "-39.420000",
            "longitude": "-71.930000",
            "elevation_m": 2847,
            "volcanic_class": None,
            "is_glaciated": False,
            "is_instrumented": True,
            "is_held_out": False,
            "image_path": None,
        },
    ]
    with patch(
        "integrations.inference.services.persist_service.db_pool.run",
        return_value=rows,
    ) as run:
        volcanoes = InferencePersistService.select_volcanoes()
    run.assert_called_once()
    assert run.call_args.args[1] == (VOLCANO_DB_FETCH_SIZE,)
    assert run.call_args.kwargs["fetch"] is PoolFetch.ALL
    assert [volcano.id for volcano in volcanoes] == ["vol-1", "vol-2"]
    assert volcanoes[0].name == "Llaima"
    assert volcanoes[0].zone is VolcanoZone.SVZ
    assert volcanoes[0].is_held_out is True
    assert volcanoes[1].name == "Villarrica"
    assert volcanoes[1].gvp_number is None
    assert volcanoes[1].is_instrumented is True


def test_select_volcanoes_uses_limit():
    with patch(
        "integrations.inference.services.persist_service.db_pool.run",
        return_value=[],
    ) as run:
        volcanoes = InferencePersistService.select_volcanoes(limit=60)
    run.assert_called_once()
    assert run.call_args.args[1] == (60,)
    assert volcanoes == []


def test_select_volcanoes_returns_empty_when_none():
    with patch(
        "integrations.inference.services.persist_service.db_pool.run",
        return_value=None,
    ) as run:
        volcanoes = InferencePersistService.select_volcanoes()
    run.assert_called_once()
    assert run.call_args.args[1] == (VOLCANO_DB_FETCH_SIZE,)
    assert run.call_args.kwargs["fetch"] is PoolFetch.ALL
    assert volcanoes == []


def test_select_interferogram_returns_none_when_ids_missing():
    with patch("integrations.inference.services.persist_service.db_pool.run") as run:
        assert InferencePersistService.select_interferogram((None, None)) is None
    run.assert_not_called()


def test_select_interferogram_maps_row():
    row = {
        "id": "ifg-1",
        "source": TrainingSampleSource.HEPHAESTUS.value,
        "split": TrainingSplit.HOLDOUT.value,
        "label": TrainingDeformationLabel.POSITIVE.value,
        "frame_id": "f1",
        "primary_at": None,
        "secondary_at": None,
        "coherence_mean": "0.800",
        "is_augmented": False,
        "storage_path": "hephaestus/abc.npz",
        "deformation_source_id": None,
        "volcano_id": "vol-1",
    }
    with patch(
        "integrations.inference.services.persist_service.db_pool.run",
        return_value=row,
    ) as run:
        interferogram = InferencePersistService.select_interferogram(("ifg-1", None))
    run.assert_called_once()
    assert run.call_args.args[1] == ("ifg-1", None)
    assert run.call_args.kwargs["fetch"] is PoolFetch.ONE
    assert interferogram.id == "ifg-1"
    assert interferogram.storage_path == "hephaestus/abc.npz"
    assert interferogram.volcano_id == "vol-1"
    assert interferogram.label is TrainingDeformationLabel.POSITIVE


def test_select_interferogram_returns_none_when_empty():
    with patch(
        "integrations.inference.services.persist_service.db_pool.run",
        return_value=None,
    ):
        assert InferencePersistService.select_interferogram(("ifg-1", None)) is None


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
        "integrations.inference.services.persist_service.db_pool.run",
        return_value=row,
    ) as run:
        deformation = InferencePersistService.select_deformation("session-1")
    assert run.call_args.args[1] == ("session-1",)
    assert run.call_args.kwargs["fetch"] is PoolFetch.ONE
    assert deformation.id == "def-1"
    assert deformation.patch_px == 8
    assert deformation.normalize is TrainingNormalize.NONE
    assert deformation.class_id == "class-1"


def test_select_deformation_returns_none_when_empty():
    with patch(
        "integrations.inference.services.persist_service.db_pool.run",
        return_value=None,
    ):
        assert InferencePersistService.select_deformation("session-1") is None


def test_upsert_deformation_passes_storage_dict():
    deformation = InferenceDeformation(
        score=Decimal("0.90000"),
        label=TrainingDeformationLabel.POSITIVE,
        threshold_used=Decimal("0.50000"),
        abstention_band=Decimal("0.00000"),
        abstained=False,
        transform_hash="a" * 64,
        op_version=1,
        inferred_at=datetime.now(timezone.utc),
        artifact_id="11111111-1111-1111-1111-111111111111",
        interferogram_id="22222222-2222-2222-2222-222222222222",
    )
    with patch("integrations.inference.services.persist_service.db_pool.run") as run:
        InferencePersistService.upsert_deformation(deformation)
    run.assert_called_once()
    params = run.call_args.args[1]
    assert "id" not in params
    assert params["score"] == Decimal("0.90000")
    assert params["label"] == TrainingDeformationLabel.POSITIVE.value
    assert params["artifact_id"] == deformation.artifact_id
    assert params["interferogram_id"] == deformation.interferogram_id


def test_select_seismic_event_returns_none_when_ids_missing():
    with patch("integrations.inference.services.persist_service.db_pool.run") as run:
        assert InferencePersistService.select_seismic_event((None, None)) is None
    run.assert_not_called()


def test_select_seismic_event_maps_row():
    recorded_at = datetime.now(timezone.utc)
    row = {
        "id": "evt-1",
        "source": TrainingSampleSource.LLAIMA.value,
        "split": TrainingSplit.HOLDOUT.value,
        "label": TrainingSeismicLabel.LP.value,
        "station": "LAV",
        "recorded_at": recorded_at,
        "duration_s": "60.000",
        "sampling_hz": 100,
        "waveform_path": "llaima/abc.npz",
        "spectrogram_path": None,
        "volcano_id": "vol-1",
    }
    with patch(
        "integrations.inference.services.persist_service.db_pool.run",
        return_value=row,
    ) as run:
        seismic_event = InferencePersistService.select_seismic_event(("evt-1", None))
    run.assert_called_once()
    assert run.call_args.args[1] == ("evt-1", None)
    assert run.call_args.kwargs["fetch"] is PoolFetch.ONE
    assert seismic_event.id == "evt-1"
    assert seismic_event.waveform_path == "llaima/abc.npz"
    assert seismic_event.volcano_id == "vol-1"
    assert seismic_event.label is TrainingSeismicLabel.LP
    assert seismic_event.sampling_hz == 100


def test_select_seismic_event_returns_none_when_empty():
    with patch(
        "integrations.inference.services.persist_service.db_pool.run",
        return_value=None,
    ):
        assert InferencePersistService.select_seismic_event(("evt-1", None)) is None


def test_select_seismic_maps_row():
    row = {
        "id": "seis-1",
        "nfft": 32,
        "hop": 16,
        "window": TrainingWindow.HANN.value,
        "window_s": "1.000",
        "sampling_hz": 100,
        "mel_bins": 8,
        "bandpass_low_hz": "1.00",
        "bandpass_high_hz": "10.00",
        "normalize": TrainingNormalize.NONE.value,
        "snr_min": "0.100",
        "class_id": "class-1",
    }
    with patch(
        "integrations.inference.services.persist_service.db_pool.run",
        return_value=row,
    ) as run:
        seismic = InferencePersistService.select_seismic("session-1")
    assert run.call_args.args[1] == ("session-1",)
    assert run.call_args.kwargs["fetch"] is PoolFetch.ONE
    assert seismic.id == "seis-1"
    assert seismic.nfft == 32
    assert seismic.window is TrainingWindow.HANN
    assert seismic.normalize is TrainingNormalize.NONE
    assert seismic.class_id == "class-1"


def test_select_seismic_returns_none_when_empty():
    with patch(
        "integrations.inference.services.persist_service.db_pool.run",
        return_value=None,
    ):
        assert InferencePersistService.select_seismic("session-1") is None


def test_upsert_seismic_passes_storage_dict():
    seismic = InferenceSeismic(
        label=TrainingSeismicLabel.TR,
        probabilities=[
            Decimal("0.05000"),
            Decimal("0.05000"),
            Decimal("0.85000"),
            Decimal("0.05000"),
        ],
        class_order=[
            TrainingSeismicLabel.VT,
            TrainingSeismicLabel.LP,
            TrainingSeismicLabel.TR,
            TrainingSeismicLabel.TC,
        ],
        threshold_used=Decimal("0.00000"),
        abstention_band=Decimal("0.00000"),
        abstained=False,
        transform_hash="b" * 64,
        op_version=1,
        inferred_at=datetime.now(timezone.utc),
        artifact_id="11111111-1111-1111-1111-111111111111",
        seismic_event_id="33333333-3333-3333-3333-333333333333",
    )
    with patch("integrations.inference.services.persist_service.db_pool.run") as run:
        InferencePersistService.upsert_seismic(seismic)
    run.assert_called_once()
    params = run.call_args.args[1]
    assert "id" not in params
    assert params["label"] == TrainingSeismicLabel.TR.value
    assert params["probabilities"] == seismic.probabilities
    assert params["artifact_id"] == seismic.artifact_id
    assert params["seismic_event_id"] == seismic.seismic_event_id
