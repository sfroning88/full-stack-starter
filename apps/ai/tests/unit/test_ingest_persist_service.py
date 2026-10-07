"""
Author: Sean Froning
Created Date: 8.21.2026
Unit tests for IngestPersistService
"""

import io
from unittest.mock import MagicMock, patch

import numpy as np
from datetime import datetime, timezone
from decimal import Decimal

from fiery_python import (
    DatasetIngest,
    TrainingDeformationSource,
    TrainingDeformationSourceType,
    TrainingInterferogram,
    TrainingDeformationLabel,
    TrainingSampleSource,
    TrainingSeismicEvent,
    TrainingSeismicLabel,
    TrainingSplit,
    TrainingStatus,
    TrainingNoiseModel,
)
from integrations.ingest.services.persist_service import IngestPersistService


def test_npz_bytes_stacks_phase_then_coherence():
    phase = np.ones((4, 4), dtype=np.float32)
    coherence = np.full((4, 4), 0.5, dtype=np.float32)
    body = IngestPersistService.interferogram_npz_bytes(phase, coherence)
    loaded = np.load(io.BytesIO(body))
    stack = loaded["data"]
    assert stack.shape == (2, 4, 4)
    np.testing.assert_array_equal(stack[0], phase)
    np.testing.assert_array_equal(stack[1], coherence)


def test_waveform_npz_bytes_stores_1d_float32():
    waveform = np.arange(8, dtype=np.float64)
    body = IngestPersistService.waveform_npz_bytes(waveform)
    loaded = np.load(io.BytesIO(body))
    trace = loaded["data"]
    assert trace.dtype == np.float32
    assert trace.shape == (8,)
    np.testing.assert_array_equal(trace, waveform.astype(np.float32))


def test_upsert_ingest_passes_storage_dict():
    ingest = DatasetIngest(
        id="11111111-1111-1111-1111-111111111111",
        source=TrainingSampleSource.HEPHAESTUS,
        status=TrainingStatus.PENDING,
    )
    with patch("integrations.ingest.services.persist_service.db_pool.run") as run:
        IngestPersistService.upsert_ingest(ingest)
    run.assert_called_once()
    params = run.call_args.args[1]
    assert params["id"] == ingest.id
    assert params["source"] == TrainingSampleSource.HEPHAESTUS.value
    assert params["status"] == TrainingStatus.PENDING.value


def test_upsert_ingest_llaima_passes_storage_dict():
    ingest = DatasetIngest(
        id="11111111-1111-1111-1111-111111111111",
        source=TrainingSampleSource.LLAIMA,
        status=TrainingStatus.PENDING,
    )
    with patch("integrations.ingest.services.persist_service.db_pool.run") as run:
        IngestPersistService.upsert_ingest(ingest)
    params = run.call_args.args[1]
    assert params["source"] == TrainingSampleSource.LLAIMA.value
    assert params["status"] == TrainingStatus.PENDING.value


def test_upsert_interferograms_execute_values():
    row = TrainingInterferogram(
        source=TrainingSampleSource.HEPHAESTUS,
        split=TrainingSplit.TRAIN,
        label=TrainingDeformationLabel.POSITIVE,
        storage_path="hephaestus/abc.npz",
    )
    cursor = MagicMock()
    with (
        patch(
            "integrations.ingest.services.persist_service.db_pool.get_cursor"
        ) as get_cursor,
        patch(
            "integrations.ingest.services.persist_service.execute_values"
        ) as execute_values,
        patch(
            "integrations.ingest.services.persist_service.UPSERT_INTERFEROGRAMS.as_string",
            return_value="INSERT",
        ),
        patch(
            "integrations.ingest.services.persist_service.UPSERT_INTERFEROGRAMS_TEMPLATE.as_string",
            return_value="TEMPLATE",
        ),
    ):
        get_cursor.return_value.__enter__.return_value = cursor
        IngestPersistService.upsert_interferograms([row])
    execute_values.assert_called_once()
    inserted = execute_values.call_args.args[2]
    assert inserted[0]["storage_path"] == "hephaestus/abc.npz"
    assert inserted[0]["id"] == row.deterministic_id()


def test_upsert_seismic_events_execute_values():
    row = TrainingSeismicEvent(
        source=TrainingSampleSource.LLAIMA,
        split=TrainingSplit.TRAIN,
        label=TrainingSeismicLabel.LP,
        station="LAV",
        recorded_at=datetime(2010, 1, 1, tzinfo=timezone.utc),
        duration_s=Decimal("60.000"),
        sampling_hz=100,
        waveform_path="llaima/abc.npz",
    )
    cursor = MagicMock()
    with (
        patch(
            "integrations.ingest.services.persist_service.db_pool.get_cursor"
        ) as get_cursor,
        patch(
            "integrations.ingest.services.persist_service.execute_values"
        ) as execute_values,
        patch(
            "integrations.ingest.services.persist_service.UPSERT_SEISMIC_EVENTS.as_string",
            return_value="INSERT",
        ),
        patch(
            "integrations.ingest.services.persist_service.UPSERT_SEISMIC_EVENTS_TEMPLATE.as_string",
            return_value="TEMPLATE",
        ),
    ):
        get_cursor.return_value.__enter__.return_value = cursor
        IngestPersistService.upsert_seismic_events([row])
    execute_values.assert_called_once()
    inserted = execute_values.call_args.args[2]
    assert inserted[0]["waveform_path"] == "llaima/abc.npz"
    assert inserted[0]["source"] == TrainingSampleSource.LLAIMA.value
    assert inserted[0]["label"] == TrainingSeismicLabel.LP.value
    assert inserted[0]["station"] == "LAV"
    assert inserted[0]["sampling_hz"] == 100
    assert inserted[0]["id"] == row.deterministic_id()


def test_upsert_deformation_sources_execute_values():
    source = TrainingDeformationSource(
        source=TrainingDeformationSourceType.OKADA,
        latitude=-38.0,
        longitude=-71.0,
        depth_km=5.0,
        los_incidence_deg=37.0,
        los_heading_deg=-10.0,
        wavelength_m=0.0555,
        noise_model=TrainingNoiseModel.NONE,
    )
    cursor = MagicMock()
    with (
        patch(
            "integrations.ingest.services.persist_service.db_pool.get_cursor"
        ) as get_cursor,
        patch(
            "integrations.ingest.services.persist_service.execute_values"
        ) as execute_values,
        patch(
            "integrations.ingest.services.persist_service.UPSERT_DEFORMATION_SOURCES.as_string",
            return_value="INSERT",
        ),
        patch(
            "integrations.ingest.services.persist_service.UPSERT_DEFORMATION_SOURCES_TEMPLATE.as_string",
            return_value="TEMPLATE",
        ),
    ):
        get_cursor.return_value.__enter__.return_value = cursor
        IngestPersistService.upsert_deformation_sources([source])
    inserted = execute_values.call_args.args[2]
    assert inserted[0]["id"] == source.deterministic_id()
    assert inserted[0]["source"] == TrainingDeformationSourceType.OKADA.value


def test_upsert_okada_page_runs_both_on_one_cursor():
    source = TrainingDeformationSource(
        source=TrainingDeformationSourceType.OKADA,
        latitude=-38.0,
        longitude=-71.0,
        depth_km=5.0,
        los_incidence_deg=37.0,
        los_heading_deg=-10.0,
        wavelength_m=0.0555,
        noise_model=TrainingNoiseModel.NONE,
    )
    source.id = source.deterministic_id()
    interferogram = TrainingInterferogram(
        source=TrainingSampleSource.OKADA,
        split=TrainingSplit.TRAIN,
        label=TrainingDeformationLabel.POSITIVE,
        storage_path="okada/abc.npz",
        deformation_source_id=source.id,
    )
    cursor = MagicMock()
    with (
        patch(
            "integrations.ingest.services.persist_service.db_pool.get_cursor"
        ) as get_cursor,
        patch(
            "integrations.ingest.services.persist_service.execute_values"
        ) as execute_values,
        patch(
            "integrations.ingest.services.persist_service.UPSERT_DEFORMATION_SOURCES.as_string",
            return_value="SOURCES",
        ),
        patch(
            "integrations.ingest.services.persist_service.UPSERT_DEFORMATION_SOURCES_TEMPLATE.as_string",
            return_value="SOURCE_TEMPLATE",
        ),
        patch(
            "integrations.ingest.services.persist_service.UPSERT_INTERFEROGRAMS.as_string",
            return_value="INTERFEROGRAMS",
        ),
        patch(
            "integrations.ingest.services.persist_service.UPSERT_INTERFEROGRAMS_TEMPLATE.as_string",
            return_value="INTERFEROGRAM_TEMPLATE",
        ),
    ):
        get_cursor.return_value.__enter__.return_value = cursor
        IngestPersistService.upsert_okada_page([source], [interferogram])
    assert get_cursor.call_count == 1
    assert execute_values.call_count == 2
    assert execute_values.call_args_list[0].args[1] == "SOURCES"
    assert execute_values.call_args_list[1].args[1] == "INTERFEROGRAMS"
    assert execute_values.call_args_list[0].args[2][0]["id"] == source.id
    assert (
        execute_values.call_args_list[1].args[2][0]["deformation_source_id"]
        == source.id
    )
