"""
Author: Sean Froning
Created Date: 8.29.2026
Unit tests for InferenceServingOrchestrator
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch

import numpy as np
import pytest
from fiery_python import error
from fiery_python import (
    InferenceDeformation,
    InferenceSeismic,
    ModelRole,
    ModelTier,
    TrainingDeformationLabel,
    TrainingSampleSource,
    TrainingSeismicLabel,
    TrainingSplit,
    TrainingInterferogram,
    TrainingSeismicEvent,
)
from integrations.inference.schemas import InferenceSingleRequest
from integrations.inference.services.serving_orchestrator import (
    InferenceServingOrchestrator,
)

IFG_ID = "22222222-2222-2222-2222-222222222222"
EVT_ID = "33333333-3333-3333-3333-333333333333"
ART_ID = "11111111-1111-1111-1111-111111111111"
VOL_ID = "44444444-4444-4444-4444-444444444444"
NOW = datetime.now(timezone.utc)
TRANSFORM_HASH = "a" * 64


def _deformation_request() -> InferenceSingleRequest:
    return InferenceSingleRequest(
        tier=ModelTier.CLOUD,
        role=ModelRole.SCREENER,
        interferogram_id=IFG_ID,
    )


def _seismic_request() -> InferenceSingleRequest:
    return InferenceSingleRequest(
        tier=ModelTier.CLOUD,
        role=ModelRole.TEACHER,
        seismic_event_id=EVT_ID,
    )


def _interferogram() -> TrainingInterferogram:
    return TrainingInterferogram(
        id=IFG_ID,
        source=TrainingSampleSource.HEPHAESTUS,
        split=TrainingSplit.HOLDOUT,
        label=TrainingDeformationLabel.POSITIVE,
        storage_path="hephaestus/abc.npz",
        volcano_id=VOL_ID,
    )


def _seismic_event() -> TrainingSeismicEvent:
    return TrainingSeismicEvent(
        id=EVT_ID,
        source=TrainingSampleSource.LLAIMA,
        split=TrainingSplit.HOLDOUT,
        label=TrainingSeismicLabel.LP,
        recorded_at=NOW,
        duration_s=Decimal("60.000"),
        sampling_hz=100,
        waveform_path="llaima/abc.npz",
        volcano_id=VOL_ID,
    )


def _deformation_row() -> InferenceDeformation:
    return InferenceDeformation(
        score=Decimal("0.90000"),
        label=TrainingDeformationLabel.POSITIVE,
        threshold_used=Decimal("0.50000"),
        abstention_band=Decimal("0.00000"),
        abstained=False,
        transform_hash=TRANSFORM_HASH,
        op_version=1,
        latency_ms=Decimal("1.000"),
        inferred_at=NOW,
        artifact_id=ART_ID,
        interferogram_id=IFG_ID,
    )


def _seismic_row() -> InferenceSeismic:
    return InferenceSeismic(
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
        transform_hash=TRANSFORM_HASH,
        op_version=1,
        latency_ms=Decimal("1.000"),
        inferred_at=NOW,
        artifact_id=ART_ID,
        seismic_event_id=EVT_ID,
    )


def _volcano_request(
    *,
    tier: ModelTier = ModelTier.CLOUD,
    role: ModelRole = ModelRole.SCREENER,
) -> InferenceSingleRequest:
    return InferenceSingleRequest(
        tier=tier,
        role=role,
        volcano_id=VOL_ID,
    )


def test_run_raises_for_unsupported_slot():
    payload = InferenceSingleRequest(
        tier=ModelTier.EDGE,
        role=ModelRole.SCREENER,
        interferogram_id=IFG_ID,
    )
    with pytest.raises(NotImplementedError):
        InferenceServingOrchestrator.run(payload)


def test_run_raises_when_sample_unselected():
    payload = InferenceSingleRequest(
        tier=ModelTier.CLOUD,
        role=ModelRole.SCREENER,
    )
    with pytest.raises(error, match="interferogram or seismic_event"):
        InferenceServingOrchestrator.run(payload)


def test_run_volcano_raises_when_interferogram_missing():
    with patch(
        "integrations.inference.services.serving_orchestrator.InferencePersistService.select_interferogram",
        return_value=None,
    ) as select_interferogram:
        with pytest.raises(error, match="No interferogram"):
            InferenceServingOrchestrator.run(_volcano_request())
    select_interferogram.assert_called_once_with((None, VOL_ID))


def test_run_volcano_raises_when_seismic_event_missing():
    with patch(
        "integrations.inference.services.serving_orchestrator.InferencePersistService.select_seismic_event",
        return_value=None,
    ) as select_event:
        with pytest.raises(error, match="No seismic event"):
            InferenceServingOrchestrator.run(_volcano_request(role=ModelRole.TEACHER))
    select_event.assert_called_once_with((None, VOL_ID))


def test_run_raises_when_interferogram_missing():
    with patch(
        "integrations.inference.services.serving_orchestrator.InferencePersistService.select_interferogram",
        return_value=None,
    ):
        with pytest.raises(error, match="No interferogram"):
            InferenceServingOrchestrator.run(_deformation_request())


def test_run_raises_when_seismic_event_missing():
    with patch(
        "integrations.inference.services.serving_orchestrator.InferencePersistService.select_seismic_event",
        return_value=None,
    ):
        with pytest.raises(error, match="No seismic event"):
            InferenceServingOrchestrator.run(_seismic_request())


def test_run_persists_deformation_and_returns_outcome():
    sample = np.zeros((2, 4, 4), dtype=np.float32)
    probabilities = {
        "negative": Decimal("0.10000"),
        "positive": Decimal("0.90000"),
    }
    row = _deformation_row()
    with (
        patch(
            "integrations.inference.services.serving_orchestrator.InferencePersistService.select_interferogram",
            return_value=_interferogram(),
        ) as select_interferogram,
        patch(
            "integrations.inference.services.serving_orchestrator.BlobStorageServices.get_unrefined",
            return_value=b"npz",
        ) as get_unrefined,
        patch(
            "integrations.inference.services.serving_orchestrator.InferencePersistService.load_npz",
            return_value=sample,
        ) as load_npz,
        patch(
            "integrations.inference.services.serving_orchestrator.InferenceServingWaiter.run",
            return_value=(row, probabilities),
        ) as waiter,
        patch(
            "integrations.inference.services.serving_orchestrator.InferencePersistService.upsert_deformation"
        ) as upsert_deformation,
        patch(
            "integrations.inference.services.serving_orchestrator.InferencePersistService.upsert_seismic"
        ) as upsert_seismic,
    ):
        response = InferenceServingOrchestrator.run(_deformation_request())
    select_interferogram.assert_called_once_with((IFG_ID, None))
    get_unrefined.assert_called_once_with("hephaestus/abc.npz")
    load_npz.assert_called_once_with(b"npz")
    waiter.assert_called_once()
    assert waiter.call_args.args[0] == (ModelTier.CLOUD, ModelRole.SCREENER)
    np.testing.assert_array_equal(waiter.call_args.args[1], sample)
    assert waiter.call_args.args[2] == IFG_ID
    assert waiter.call_args.args[3] is None
    upsert_deformation.assert_called_once_with(row)
    upsert_seismic.assert_not_called()
    assert response.artifact_id == ART_ID
    assert response.transform_hash == TRANSFORM_HASH
    outcome = response.result
    assert outcome.label is TrainingDeformationLabel.POSITIVE
    assert outcome.score == Decimal("0.90000")
    assert outcome.interferogram_id == IFG_ID
    assert outcome.seismic_event_id is None
    assert outcome.volcano_id == VOL_ID
    assert outcome.probabilities == probabilities


def test_run_persists_seismic_and_returns_outcome():
    sample = np.zeros(100, dtype=np.float32)
    probabilities = {
        "vt": Decimal("0.05000"),
        "lp": Decimal("0.05000"),
        "tr": Decimal("0.85000"),
        "tc": Decimal("0.05000"),
    }
    row = _seismic_row()
    with (
        patch(
            "integrations.inference.services.serving_orchestrator.InferencePersistService.select_seismic_event",
            return_value=_seismic_event(),
        ) as select_event,
        patch(
            "integrations.inference.services.serving_orchestrator.BlobStorageServices.get_unrefined",
            return_value=b"npz",
        ) as get_unrefined,
        patch(
            "integrations.inference.services.serving_orchestrator.InferencePersistService.load_npz",
            return_value=sample,
        ),
        patch(
            "integrations.inference.services.serving_orchestrator.InferenceServingWaiter.run",
            return_value=(row, probabilities),
        ) as waiter,
        patch(
            "integrations.inference.services.serving_orchestrator.InferencePersistService.upsert_deformation"
        ) as upsert_deformation,
        patch(
            "integrations.inference.services.serving_orchestrator.InferencePersistService.upsert_seismic"
        ) as upsert_seismic,
    ):
        response = InferenceServingOrchestrator.run(_seismic_request())
    select_event.assert_called_once_with((EVT_ID, None))
    get_unrefined.assert_called_once_with("llaima/abc.npz")
    waiter.assert_called_once()
    assert waiter.call_args.args[0] == (ModelTier.CLOUD, ModelRole.TEACHER)
    np.testing.assert_array_equal(waiter.call_args.args[1], sample)
    assert waiter.call_args.args[2] is None
    assert waiter.call_args.args[3] == EVT_ID
    upsert_seismic.assert_called_once_with(row)
    upsert_deformation.assert_not_called()
    outcome = response.result
    assert outcome.label is TrainingSeismicLabel.TR
    assert outcome.score is None
    assert outcome.interferogram_id is None
    assert outcome.seismic_event_id == EVT_ID
    assert outcome.volcano_id == VOL_ID
    assert outcome.probabilities == probabilities


def test_run_volcano_resolves_latest_interferogram_once():
    sample = np.zeros((2, 4, 4), dtype=np.float32)
    row = _deformation_row()
    with (
        patch(
            "integrations.inference.services.serving_orchestrator.InferencePersistService.select_interferogram",
            return_value=_interferogram(),
        ) as select_interferogram,
        patch(
            "integrations.inference.services.serving_orchestrator.BlobStorageServices.get_unrefined",
            return_value=b"npz",
        ),
        patch(
            "integrations.inference.services.serving_orchestrator.InferencePersistService.load_npz",
            return_value=sample,
        ),
        patch(
            "integrations.inference.services.serving_orchestrator.InferenceServingWaiter.run",
            return_value=(row, {"positive": Decimal("0.90000")}),
        ) as waiter,
        patch(
            "integrations.inference.services.serving_orchestrator.InferencePersistService.upsert_deformation"
        ),
        patch(
            "integrations.inference.services.serving_orchestrator.InferencePersistService.upsert_seismic"
        ),
    ):
        response = InferenceServingOrchestrator.run(_volcano_request())
    select_interferogram.assert_called_once_with((None, VOL_ID))
    assert waiter.call_args.args[2] == IFG_ID
    assert waiter.call_args.args[3] is None
    assert response.result.interferogram_id == IFG_ID
    assert response.result.seismic_event_id is None
    assert response.result.volcano_id == VOL_ID


def test_run_volcano_resolves_latest_seismic_event_once():
    sample = np.zeros(100, dtype=np.float32)
    row = _seismic_row()
    with (
        patch(
            "integrations.inference.services.serving_orchestrator.InferencePersistService.select_seismic_event",
            return_value=_seismic_event(),
        ) as select_event,
        patch(
            "integrations.inference.services.serving_orchestrator.BlobStorageServices.get_unrefined",
            return_value=b"npz",
        ),
        patch(
            "integrations.inference.services.serving_orchestrator.InferencePersistService.load_npz",
            return_value=sample,
        ),
        patch(
            "integrations.inference.services.serving_orchestrator.InferenceServingWaiter.run",
            return_value=(row, {"tr": Decimal("0.85000")}),
        ) as waiter,
        patch(
            "integrations.inference.services.serving_orchestrator.InferencePersistService.upsert_deformation"
        ),
        patch(
            "integrations.inference.services.serving_orchestrator.InferencePersistService.upsert_seismic"
        ),
    ):
        response = InferenceServingOrchestrator.run(
            _volcano_request(role=ModelRole.TEACHER)
        )
    select_event.assert_called_once_with((None, VOL_ID))
    assert waiter.call_args.args[2] is None
    assert waiter.call_args.args[3] == EVT_ID
    assert response.result.interferogram_id is None
    assert response.result.seismic_event_id == EVT_ID
    assert response.result.volcano_id == VOL_ID
