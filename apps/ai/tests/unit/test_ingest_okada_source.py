"""
Author: Sean Froning
Created Date: 8.21.2026
Unit tests for IngestOkadaSource
"""

from unittest.mock import patch

import numpy as np
import pytest
from fiery_python import (
    TrainingDeformationLabel,
    TrainingDeformationSource,
    TrainingInterferogram,
    TrainingSampleSource,
    TrainingStatus,
)
from integrations.ingest.services.okada_source import (
    IngestOkadaSource,
    _PATCH_PX,
)


def test_forward_phase_shape_and_coherence():
    phase, coherence = IngestOkadaSource._forward_phase(0.5)
    assert phase.shape == (_PATCH_PX, _PATCH_PX)
    assert coherence.shape == (_PATCH_PX, _PATCH_PX)
    assert np.all(coherence == 0.85)
    assert float(np.max(np.abs(phase))) <= np.pi + 1e-5


def test_forward_phase_zero_slip_is_flat():
    phase, _coherence = IngestOkadaSource._forward_phase(0.0)
    np.testing.assert_allclose(phase, 0.0, atol=1e-6)


def test_iter_samples_unique_sources_and_labels():
    samples = list(IngestOkadaSource._iter_samples(max_samples=5))
    assert len(samples) == 5
    ids = {sample["source"].id for sample in samples}
    assert len(ids) == 5
    negatives = [
        sample
        for sample in samples
        if sample["label"] is TrainingDeformationLabel.NEGATIVE
    ]
    assert len(negatives) >= 1
    assert all(
        sample["source"].id == sample["source"].deterministic_id() for sample in samples
    )


def test_run_upserts_okada_page():
    samples = list(IngestOkadaSource._iter_samples(max_samples=2))

    def _record_page(sources, interferograms):
        assert len(sources) == 2
        assert len(interferograms) == 2
        assert isinstance(sources[0], TrainingDeformationSource)
        assert isinstance(interferograms[0], TrainingInterferogram)
        assert interferograms[0].deformation_source_id == samples[0]["source"].id

    with (
        patch.object(IngestOkadaSource, "_iter_samples", return_value=samples),
        patch(
            "integrations.ingest.services.okada_source.IngestPersistService.upsert_ingest"
        ) as upsert_ingest,
        patch(
            "integrations.ingest.services.okada_source.IngestPersistService.upsert_okada_page",
            side_effect=_record_page,
        ) as upsert_okada_page,
        patch(
            "integrations.ingest.services.okada_source.IngestPersistService.interferogram_npz_bytes",
            return_value=b"npz",
        ),
        patch(
            "integrations.ingest.services.okada_source.BlobStorageServices.put_unrefined",
            return_value="okada/abc.npz",
        ),
    ):
        count = IngestOkadaSource.run("ingest-okada", max_samples=2)
    assert count == 2
    upsert_okada_page.assert_called_once()
    assert upsert_ingest.call_args_list[-1].args[0].status == TrainingStatus.COMPLETED
    assert upsert_ingest.call_args_list[-1].args[0].source == TrainingSampleSource.OKADA


def test_run_marks_failed_and_reraises():
    with (
        patch.object(
            IngestOkadaSource, "_iter_samples", side_effect=RuntimeError("synth")
        ),
        patch(
            "integrations.ingest.services.okada_source.IngestPersistService.upsert_ingest"
        ) as upsert_ingest,
    ):
        with pytest.raises(RuntimeError, match="synth"):
            IngestOkadaSource.run("ingest-okada", max_samples=1)
    assert upsert_ingest.call_args_list[-1].args[0].status == TrainingStatus.FAILED


def test_run_passes_max_samples_through():
    with (
        patch.object(
            IngestOkadaSource, "_iter_samples", return_value=[]
        ) as iter_samples,
        patch(
            "integrations.ingest.services.okada_source.IngestPersistService.upsert_ingest"
        ),
    ):
        IngestOkadaSource.run("ingest-okada", max_samples=1)
        IngestOkadaSource.run("ingest-okada", max_samples=50)
    assert iter_samples.call_args_list[0].args == (1,)
    assert iter_samples.call_args_list[1].args == (50,)


def test_run_rejects_non_positive_max_samples():
    with pytest.raises(ValueError, match="max_samples must be positive"):
        IngestOkadaSource.run("ingest-okada", max_samples=0)
    with pytest.raises(ValueError, match="max_samples must be positive"):
        IngestOkadaSource.run("ingest-okada", max_samples=-1)
