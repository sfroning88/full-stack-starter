"""
Author: Sean Froning
Created Date: 8.28.2026
Unit tests for IngestLlaimaSource
"""

from datetime import datetime, timezone
from unittest.mock import patch

import numpy as np
import pytest
from fiery_python import (
    TrainingSampleSource,
    TrainingSeismicLabel,
    TrainingSplit,
    TrainingStatus,
)
from integrations.ingest.services.llaima_source import (
    IngestLlaimaSource,
    _RECORDED_EPOCH,
)

_TRACE_LEN = 6000


def _llaima_row(
    *,
    label=0,
    station="LAV",
    sampling_hz=100,
    fill=1.5,
):
    waveform = np.full(_TRACE_LEN, fill, dtype=np.float32)
    return {
        "waveform": waveform,
        "label": label,
        "station": station,
        "sampling_hz": sampling_hz,
        "duration_s": float(_TRACE_LEN / sampling_hz),
    }


class MagicIter:
    def __init__(self, rows):
        self._rows = rows
        self.taken = None

    def take(self, n):
        self.taken = n
        return self

    def __iter__(self):
        return iter(self._rows)


def test_waveform_from_event_squeezes_column():
    row = {"waveform": np.ones((_TRACE_LEN, 1), dtype=np.float32)}
    got = IngestLlaimaSource._waveform_from_event(row)
    assert got is not None
    assert got.shape == (_TRACE_LEN,)
    assert got.dtype == np.float32


def test_waveform_from_event_returns_none_when_missing():
    assert IngestLlaimaSource._waveform_from_event({}) is None
    assert IngestLlaimaSource._waveform_from_event(None) is None
    assert (
        IngestLlaimaSource._waveform_from_event({"waveform": np.ones((2, 3))}) is None
    )


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"label": 0}, TrainingSeismicLabel.VT),
        ({"label": 1}, TrainingSeismicLabel.LP),
        ({"label": 2}, TrainingSeismicLabel.TR),
        ({"label": 3}, TrainingSeismicLabel.TC),
        ({"label": "vt"}, TrainingSeismicLabel.VT),
        ({"label": "LP"}, TrainingSeismicLabel.LP),
        ({"label": 4}, None),
        ({"label": "unknown"}, None),
        ({}, None),
    ],
)
def test_label_from_event(payload, expected):
    assert IngestLlaimaSource._label_from_event(payload) == expected


def test_recorded_at_from_event_offsets_epoch():
    got = IngestLlaimaSource._recorded_at_from_event(3)
    assert got == datetime(2010, 1, 1, 0, 0, 3, tzinfo=timezone.utc)
    assert got == _RECORDED_EPOCH.replace(second=3)


def test_iter_samples_skips_bad_rows():
    rows_by_split = {
        "train": [
            _llaima_row(label=0),
            {},
            _llaima_row(label=4),
        ]
    }
    datasets = {}

    def load_dataset(*_args, **kwargs):
        fake = MagicIter(rows_by_split.get(kwargs["split"], []))
        datasets[kwargs["split"]] = fake
        return fake

    with (
        patch(
            "integrations.ingest.services.llaima_source.load_dataset",
            side_effect=load_dataset,
        ),
        patch(
            "integrations.ingest.services.llaima_source.HF_TOKEN",
            "test-token",
        ),
    ):
        samples = list(IngestLlaimaSource._iter_samples(max_samples=3))
    assert datasets["train"].taken == 3
    assert len(samples) == 1
    assert samples[0]["label"] == TrainingSeismicLabel.VT
    assert samples[0]["split"] == TrainingSplit.TRAIN
    assert samples[0]["station"] == "LAV"
    assert samples[0]["sampling_hz"] == 100
    assert samples[0]["duration_s"] == 60.0
    assert samples[0]["waveform"].shape == (_TRACE_LEN,)


def test_iter_samples_maps_hub_splits():
    rows_by_split = {
        "train": [_llaima_row(label=0)],
        "validation": [_llaima_row(label=1)],
        "test": [_llaima_row(label="tc")],
    }

    def load_dataset(*_args, **kwargs):
        return MagicIter(rows_by_split.get(kwargs["split"], []))

    with (
        patch(
            "integrations.ingest.services.llaima_source.load_dataset",
            side_effect=load_dataset,
        ) as load_ds,
        patch(
            "integrations.ingest.services.llaima_source.HF_TOKEN",
            "test-token",
        ),
    ):
        samples = list(IngestLlaimaSource._iter_samples(max_samples=3))
    assert [call.kwargs["split"] for call in load_ds.call_args_list] == [
        "train",
        "validation",
        "test",
    ]
    assert [(row["split"], row["label"]) for row in samples] == [
        (TrainingSplit.TRAIN, TrainingSeismicLabel.VT),
        (TrainingSplit.VALIDATE, TrainingSeismicLabel.LP),
        (TrainingSplit.TEST, TrainingSeismicLabel.TC),
    ]


def test_iter_samples_stops_after_max_samples():
    loaded = []

    def load_dataset(*_args, **kwargs):
        loaded.append(kwargs["split"])
        return MagicIter([_llaima_row(label=0)])

    with (
        patch(
            "integrations.ingest.services.llaima_source.load_dataset",
            side_effect=load_dataset,
        ),
        patch(
            "integrations.ingest.services.llaima_source.HF_TOKEN",
            "test-token",
        ),
    ):
        samples = list(IngestLlaimaSource._iter_samples(max_samples=1))
    assert loaded == ["train"]
    assert len(samples) == 1


def test_run_upserts_completed_and_returns_count():
    waveform = np.ones(_TRACE_LEN, dtype=np.float32)
    samples = [
        {
            "waveform": waveform,
            "label": TrainingSeismicLabel.LP,
            "split": TrainingSplit.TRAIN,
            "station": "LAV",
            "sampling_hz": 100,
            "duration_s": 60.0,
            "recorded_at": _RECORDED_EPOCH,
        }
    ]
    with (
        patch.object(IngestLlaimaSource, "_iter_samples", return_value=samples),
        patch(
            "integrations.ingest.services.llaima_source.IngestPersistService.upsert_ingest"
        ) as upsert_ingest,
        patch(
            "integrations.ingest.services.llaima_source.IngestPersistService.upsert_seismic_events"
        ) as upsert_events,
        patch(
            "integrations.ingest.services.llaima_source.IngestPersistService.waveform_npz_bytes",
            return_value=b"npz",
        ),
        patch(
            "integrations.ingest.services.llaima_source.BlobStorageServices.put_unrefined",
            return_value="llaima/abc.npz",
        ),
    ):
        count = IngestLlaimaSource.run("ingest-1", max_samples=1)
    assert count == 1
    assert upsert_ingest.call_args_list[0].args[0].status == TrainingStatus.EXECUTING
    assert upsert_ingest.call_args_list[-1].args[0].status == TrainingStatus.COMPLETED
    rows = upsert_events.call_args.args[0]
    assert rows[0].waveform_path == "llaima/abc.npz"
    assert rows[0].source == TrainingSampleSource.LLAIMA
    assert rows[0].label == TrainingSeismicLabel.LP
    assert rows[0].station == "LAV"


def test_run_marks_failed_and_reraises():
    with (
        patch.object(
            IngestLlaimaSource,
            "_iter_samples",
            side_effect=RuntimeError("hf down"),
        ),
        patch(
            "integrations.ingest.services.llaima_source.IngestPersistService.upsert_ingest"
        ) as upsert_ingest,
    ):
        with pytest.raises(RuntimeError, match="hf down"):
            IngestLlaimaSource.run("ingest-1", max_samples=1)
    assert upsert_ingest.call_args_list[-1].args[0].status == TrainingStatus.FAILED


def test_run_passes_max_samples_through():
    with (
        patch.object(
            IngestLlaimaSource, "_iter_samples", return_value=[]
        ) as iter_samples,
        patch(
            "integrations.ingest.services.llaima_source.IngestPersistService.upsert_ingest"
        ),
    ):
        IngestLlaimaSource.run("ingest-1", max_samples=1)
        IngestLlaimaSource.run("ingest-1", max_samples=50)
    assert iter_samples.call_args_list[0].args == (1,)
    assert iter_samples.call_args_list[1].args == (50,)


def test_run_rejects_non_positive_max_samples():
    with pytest.raises(ValueError, match="max_samples must be positive"):
        IngestLlaimaSource.run("ingest-1", max_samples=0)
    with pytest.raises(ValueError, match="max_samples must be positive"):
        IngestLlaimaSource.run("ingest-1", max_samples=-1)
