"""
Author: Sean Froning
Created Date: 8.21.2026
Unit tests for IngestHephaestusSource
"""

from datetime import date
from unittest.mock import patch

import numpy as np
import pytest
from fiery_python import (
    TrainingDeformationLabel,
    TrainingSampleSource,
    TrainingSplit,
    TrainingStatus,
)
from integrations.ingest.services.hephaestus_source import IngestHephaestusSource

_IMAGE_SHAPE = (9, 512, 512)
_MASK_SHAPE = (1, 512, 512)
_FRAME_ID = "079D_07694_131313"
_PRIMARY = "20170221"
_SECONDARY = "20170329"


def _thalia_sample(
    *,
    label="Deformation",
    corrupted=0,
    low_coherence=0,
    no_info=0,
    frame_id=_FRAME_ID,
    phase_fill=0.3,
    coherence_fill=0.8,
    class_id=0,
):
    cube = np.zeros(_IMAGE_SHAPE, dtype=np.float32)
    cube[0] = phase_fill
    cube[1] = coherence_fill
    return {
        "image.pth": cube,
        "labels.pth": np.zeros(_MASK_SHAPE, dtype=np.int64),
        "sample.pth": {
            "frame_id": frame_id,
            "insar_path": [
                "/mnt/nvme1/npapadopoulos/Hephaestus_Tiff/"
                f"{frame_id}/interferograms/{_PRIMARY}_{_SECONDARY}/"
                f"{_PRIMARY}_{_SECONDARY}.geo.diff_pha.tif"
            ],
            "annotation": [
                {
                    "uniqueID": 11645,
                    "frameID": frame_id,
                    "primary_date": _PRIMARY,
                    "secondary_date": _SECONDARY,
                    "corrupted": corrupted,
                    "processing_error": 0,
                    "glacier_fringes": 0,
                    "orbital_fringes": 0,
                    "atmospheric_fringes": 3,
                    "low_coherence": low_coherence,
                    "no_info": no_info,
                    "image_artifacts": 0,
                    "label": [label],
                    "activity_type": [],
                    "intensity_level": [],
                    "phase": "Rest",
                    "confidence": 0.8,
                    "segmentation_mask": [],
                    "is_crowd": 0,
                    "caption": "No deformation activity can be detected.",
                }
            ],
            "label": [class_id],
            "annotation_path": [
                "/mnt/shared_storage/npapadopoulos/datasets/"
                "Hephaestus_annotations/annotations/11645.json"
            ],
        },
    }


def test_channels_maps_image_pth_bands():
    sample = _thalia_sample(phase_fill=0.3, coherence_fill=200.0)
    got_phase, got_coherence = IngestHephaestusSource._channels_from_interferogram(
        sample
    )
    assert got_phase.shape == (512, 512)
    assert got_coherence.shape == (512, 512)
    np.testing.assert_allclose(got_phase, 0.3)
    np.testing.assert_allclose(got_coherence, 200.0 / 255.0)


def test_channels_returns_none_when_missing():
    assert IngestHephaestusSource._channels_from_interferogram({}) is None


def test_channels_returns_none_when_too_few_bands():
    sample = _thalia_sample()
    sample["image.pth"] = np.ones((1, 512, 512), dtype=np.float32)
    assert IngestHephaestusSource._channels_from_interferogram(sample) is None


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"label": ["Deformation"]}, TrainingDeformationLabel.POSITIVE),
        ({"label": ["Non_Deformation"]}, TrainingDeformationLabel.NEGATIVE),
        ({"label": ["Earthquake"]}, TrainingDeformationLabel.UNCERTAIN),
        ({"label": ["Deformation"], "corrupted": 1}, None),
        ({"json": {"label": "Non_Deformation"}}, TrainingDeformationLabel.NEGATIVE),
        (
            _thalia_sample(label="Non_Deformation"),
            TrainingDeformationLabel.NEGATIVE,
        ),
        (_thalia_sample(label="Deformation", corrupted=1), None),
    ],
)
def test_label_interferogram(payload, expected):
    assert IngestHephaestusSource._label_interferogram(payload) == expected


def test_parse_yyyymmdd():
    assert IngestHephaestusSource._parse_yyyymmdd("20170221") == date(2017, 2, 21)
    assert IngestHephaestusSource._parse_yyyymmdd("bad") is None


def test_iter_samples_skips_bad_rows():
    rows_by_split = {
        "train": [
            _thalia_sample(label="Deformation", frame_id=_FRAME_ID),
            {},
            _thalia_sample(label="Deformation", corrupted=1),
        ]
    }
    datasets = {}

    def load_dataset(*_args, **kwargs):
        fake = MagicIter(rows_by_split.get(kwargs["split"], []))
        datasets[kwargs["split"]] = fake
        return fake

    with (
        patch(
            "integrations.ingest.services.hephaestus_source.load_dataset",
            side_effect=load_dataset,
        ),
        patch(
            "integrations.ingest.services.hephaestus_source.HF_TOKEN",
            "test-token",
        ),
    ):
        samples = list(IngestHephaestusSource._iter_samples(max_samples=3))
    assert datasets["train"].taken == 3
    assert len(samples) == 1
    assert samples[0]["label"] == TrainingDeformationLabel.POSITIVE
    assert samples[0]["split"] == TrainingSplit.TRAIN
    assert samples[0]["frame_id"] == _FRAME_ID
    assert samples[0]["primary_at"] == date(2017, 2, 21)
    assert samples[0]["secondary_at"] == date(2017, 3, 29)
    assert samples[0]["phase"].shape == (512, 512)


def test_iter_samples_maps_hub_splits():
    rows_by_split = {
        "train": [_thalia_sample(label="Deformation", frame_id="train-1")],
        "validation": [_thalia_sample(label="Non_Deformation", frame_id="val-1")],
        "test": [_thalia_sample(label="Earthquake", frame_id="test-1")],
    }

    def load_dataset(*_args, **kwargs):
        return MagicIter(rows_by_split.get(kwargs["split"], []))

    with (
        patch(
            "integrations.ingest.services.hephaestus_source.load_dataset",
            side_effect=load_dataset,
        ) as load_ds,
        patch(
            "integrations.ingest.services.hephaestus_source.HF_TOKEN",
            "test-token",
        ),
    ):
        samples = list(IngestHephaestusSource._iter_samples(max_samples=3))
    assert [call.kwargs["split"] for call in load_ds.call_args_list] == [
        "train",
        "validation",
        "test",
    ]
    assert [(row["frame_id"], row["split"], row["label"]) for row in samples] == [
        ("train-1", TrainingSplit.TRAIN, TrainingDeformationLabel.POSITIVE),
        ("val-1", TrainingSplit.VALIDATE, TrainingDeformationLabel.NEGATIVE),
        ("test-1", TrainingSplit.TEST, TrainingDeformationLabel.UNCERTAIN),
    ]


def test_iter_samples_stops_after_max_samples():
    loaded = []

    def load_dataset(*_args, **kwargs):
        loaded.append(kwargs["split"])
        return MagicIter([_thalia_sample(frame_id=kwargs["split"])])

    with (
        patch(
            "integrations.ingest.services.hephaestus_source.load_dataset",
            side_effect=load_dataset,
        ),
        patch(
            "integrations.ingest.services.hephaestus_source.HF_TOKEN",
            "test-token",
        ),
    ):
        samples = list(IngestHephaestusSource._iter_samples(max_samples=1))
    assert loaded == ["train"]
    assert len(samples) == 1
    assert samples[0]["frame_id"] == "train"


def test_run_upserts_completed_and_returns_count():
    phase = np.ones((512, 512), dtype=np.float32)
    coherence = np.full((512, 512), 0.9, dtype=np.float32)
    samples = [
        {
            "phase": phase,
            "coherence": coherence,
            "split": TrainingSplit.TRAIN,
            "label": TrainingDeformationLabel.POSITIVE,
            "frame_id": _FRAME_ID,
            "primary_at": date(2017, 2, 21),
            "secondary_at": date(2017, 3, 29),
            "coherence_mean": 0.9,
        }
    ]
    with (
        patch.object(IngestHephaestusSource, "_iter_samples", return_value=samples),
        patch(
            "integrations.ingest.services.hephaestus_source.IngestPersistService.upsert_ingest"
        ) as upsert_ingest,
        patch(
            "integrations.ingest.services.hephaestus_source.IngestPersistService.upsert_interferograms"
        ) as upsert_interferograms,
        patch(
            "integrations.ingest.services.hephaestus_source.IngestPersistService.interferogram_npz_bytes",
            return_value=b"npz",
        ),
        patch(
            "integrations.ingest.services.hephaestus_source.BlobStorageServices.put_unrefined",
            return_value="hephaestus/abc.npz",
        ),
    ):
        count = IngestHephaestusSource.run("ingest-1", max_samples=1)
    assert count == 1
    assert upsert_ingest.call_args_list[0].args[0].status == TrainingStatus.EXECUTING
    assert upsert_ingest.call_args_list[-1].args[0].status == TrainingStatus.COMPLETED
    rows = upsert_interferograms.call_args.args[0]
    assert rows[0].storage_path == "hephaestus/abc.npz"
    assert rows[0].source == TrainingSampleSource.HEPHAESTUS
    assert rows[0].frame_id == _FRAME_ID


def test_run_marks_failed_and_reraises():
    with (
        patch.object(
            IngestHephaestusSource,
            "_iter_samples",
            side_effect=RuntimeError("hf down"),
        ),
        patch(
            "integrations.ingest.services.hephaestus_source.IngestPersistService.upsert_ingest"
        ) as upsert_ingest,
    ):
        with pytest.raises(RuntimeError, match="hf down"):
            IngestHephaestusSource.run("ingest-1", max_samples=1)
    assert upsert_ingest.call_args_list[-1].args[0].status == TrainingStatus.FAILED


def test_run_passes_max_samples_through():
    with (
        patch.object(
            IngestHephaestusSource, "_iter_samples", return_value=[]
        ) as iter_samples,
        patch(
            "integrations.ingest.services.hephaestus_source.IngestPersistService.upsert_ingest"
        ),
    ):
        IngestHephaestusSource.run("ingest-1", max_samples=1)
        IngestHephaestusSource.run("ingest-1", max_samples=50)
    assert iter_samples.call_args_list[0].args == (1,)
    assert iter_samples.call_args_list[1].args == (50,)


def test_run_rejects_non_positive_max_samples():
    with pytest.raises(ValueError, match="max_samples must be positive"):
        IngestHephaestusSource.run("ingest-1", max_samples=0)
    with pytest.raises(ValueError, match="max_samples must be positive"):
        IngestHephaestusSource.run("ingest-1", max_samples=-1)


class MagicIter:
    def __init__(self, rows):
        self._rows = rows
        self.taken = None

    def take(self, n):
        self.taken = n
        return self

    def __iter__(self):
        return iter(self._rows)
