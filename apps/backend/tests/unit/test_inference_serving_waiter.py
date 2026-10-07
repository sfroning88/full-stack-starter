"""
Author: Sean Froning
Created Date: 8.29.2026
Unit tests for InferenceServingWaiter
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import torch
import torch.nn as nn
from fiery_python import error
from fiery_python import (
    STORAGE_OP_VERSION,
    InferenceAbstainReason,
    InferenceSeismic,
    ModelRole,
    ModelTier,
    TrainingDeformation,
    TrainingDeformationLabel,
    TrainingNormalize,
    TrainingPrecision,
    TrainingSeismic,
    TrainingSeismicLabel,
    TrainingStage,
    TrainingWindow,
    Transformation,
    TransformationRejected,
)
from integrations.inference.services.serving_waiter import InferenceServingWaiter
from ml.models import LoadedModel

KEY = (ModelTier.CLOUD, ModelRole.SCREENER)
SEISMIC_KEY = (ModelTier.CLOUD, ModelRole.TEACHER)
NOW = datetime.now(timezone.utc)


def _deformation() -> TrainingDeformation:
    return TrainingDeformation(
        patch_px=4,
        wrap_rad=Decimal("3.14159"),
        normalize=TrainingNormalize.NONE,
        coherence_min=Decimal("0.300"),
        class_id="class-1",
    )


def _loaded(deformation: TrainingDeformation, **overrides) -> LoadedModel:
    preprocessing = {
        "threshold": "0.50000",
        "abstention_band": "0.00000",
        "transform_hash": Transformation.transform_hash_deformation(deformation),
        "op_version": STORAGE_OP_VERSION,
    }
    preprocessing.update(overrides.pop("preprocessing", {}))
    return LoadedModel(
        artifact_id="art-1",
        tier=ModelTier.CLOUD,
        role=ModelRole.SCREENER,
        stage=TrainingStage.LORA,
        precision=TrainingPrecision.FP32,
        architecture="vit_small_patch16_224.augreg_in21k_ft_in1k",
        param_count=1,
        sparsity=Decimal("0.0"),
        storage_path="cloud/screener/art-1.safetensors",
        signature="sig",
        signed_at=NOW,
        promoted=True,
        promoted_at=NOW,
        session_id="session-1",
        preprocessing=preprocessing,
        **overrides,
    )


def _sample() -> np.ndarray:
    phase = np.zeros((8, 8), dtype=np.float32)
    coherence = np.ones((8, 8), dtype=np.float32)
    return np.stack([phase, coherence])


class _StubModel(nn.Module):
    def __init__(self, logits: torch.Tensor) -> None:
        super().__init__()
        self.logits = logits

    def forward(self, tensor: torch.Tensor) -> torch.Tensor:
        return self.logits.unsqueeze(0).expand(tensor.shape[0], -1)


def _registry(ready: bool, metadata: LoadedModel | None, model: nn.Module | None):
    registry = MagicMock()
    registry.is_ready.return_value = ready
    registry.get.return_value = model
    registry.get_metadata.return_value = metadata.model_dump() if metadata else {}
    return registry


def test_run_raises_when_slot_not_ready():
    registry = _registry(False, None, None)
    with patch(
        "integrations.inference.services.serving_waiter.model_registry", registry
    ):
        with pytest.raises(error, match="is_ready"):
            InferenceServingWaiter.run(KEY, _sample(), "ifg-1", None)
    registry.get.assert_not_called()


def test_run_raises_when_deformation_missing():
    deformation = _deformation()
    registry = _registry(True, _loaded(deformation), _StubModel(torch.zeros(2)))
    with (
        patch(
            "integrations.inference.services.serving_waiter.model_registry",
            registry,
        ),
        patch(
            "integrations.inference.services.serving_waiter.InferencePersistService.select_deformation",
            return_value=None,
        ),
    ):
        with pytest.raises(error, match="training_deformation"):
            InferenceServingWaiter.run(KEY, _sample(), "ifg-1", None)


def test_run_raises_on_contract_mismatch():
    deformation = _deformation()
    loaded = _loaded(deformation, preprocessing={"op_version": STORAGE_OP_VERSION + 1})
    registry = _registry(True, loaded, _StubModel(torch.zeros(2)))
    with (
        patch(
            "integrations.inference.services.serving_waiter.model_registry",
            registry,
        ),
        patch(
            "integrations.inference.services.serving_waiter.InferencePersistService.select_deformation",
            return_value=deformation,
        ),
    ):
        with pytest.raises(error, match="mismatch"):
            InferenceServingWaiter.run(KEY, _sample(), "ifg-1", None)


def test_run_abstains_when_transformation_rejected():
    deformation = _deformation()
    loaded = _loaded(deformation)
    model = _StubModel(torch.tensor([0.0, 10.0]))
    registry = _registry(True, loaded, model)
    with (
        patch(
            "integrations.inference.services.serving_waiter.model_registry",
            registry,
        ),
        patch(
            "integrations.inference.services.serving_waiter.InferencePersistService.select_deformation",
            return_value=deformation,
        ),
        patch(
            "integrations.inference.services.serving_waiter.Transformation.apply_deformation",
            side_effect=TransformationRejected("coherence below min"),
        ),
    ):
        result, probabilities = InferenceServingWaiter.run(
            KEY, _sample(), "ifg-1", None
        )
    assert result.abstained is True
    assert result.abstained_reason is InferenceAbstainReason.LOW_COHERENCE
    assert result.label is None
    assert result.score is None
    assert probabilities == {}
    assert result.artifact_id == "art-1"
    assert result.interferogram_id == "ifg-1"
    assert result.latency_ms is not None


def test_run_returns_positive_when_score_beats_threshold():
    deformation = _deformation()
    loaded = _loaded(deformation)
    model = _StubModel(torch.tensor([0.0, 10.0]))
    registry = _registry(True, loaded, model)
    with (
        patch(
            "integrations.inference.services.serving_waiter.model_registry",
            registry,
        ),
        patch(
            "integrations.inference.services.serving_waiter.InferencePersistService.select_deformation",
            return_value=deformation,
        ),
    ):
        result, probabilities = InferenceServingWaiter.run(
            KEY, _sample(), "ifg-1", None
        )
    assert result.abstained is False
    assert result.label is TrainingDeformationLabel.POSITIVE
    assert result.score is not None
    assert result.score > Decimal("0.5")
    assert "positive" in probabilities
    assert "negative" in probabilities


def test_run_abstains_inside_confidence_band():
    deformation = _deformation()
    loaded = _loaded(
        deformation,
        preprocessing={"threshold": "0.50000", "abstention_band": "0.40000"},
    )
    model = _StubModel(torch.zeros(2))
    registry = _registry(True, loaded, model)
    with (
        patch(
            "integrations.inference.services.serving_waiter.model_registry",
            registry,
        ),
        patch(
            "integrations.inference.services.serving_waiter.InferencePersistService.select_deformation",
            return_value=deformation,
        ),
    ):
        result, probabilities = InferenceServingWaiter.run(
            KEY, _sample(), "ifg-1", None
        )
    assert result.abstained is True
    assert result.abstained_reason is InferenceAbstainReason.LOW_CONFIDENCE
    assert result.label is None
    assert probabilities["positive"] == probabilities["negative"]


def _seismic() -> TrainingSeismic:
    return TrainingSeismic(
        nfft=32,
        hop=16,
        window=TrainingWindow.HANN,
        window_s=Decimal("1"),
        sampling_hz=100,
        mel_bins=8,
        bandpass_low_hz=Decimal("1.00"),
        bandpass_high_hz=Decimal("10.00"),
        normalize=TrainingNormalize.NONE,
        snr_min=Decimal("0.1"),
        class_id="class-1",
    )


def _loaded_seismic(seismic: TrainingSeismic, **overrides) -> LoadedModel:
    preprocessing = {
        "threshold": "0.00000",
        "abstention_band": "0.00000",
        "transform_hash": Transformation.transform_hash_seismic(seismic),
        "op_version": STORAGE_OP_VERSION,
    }
    preprocessing.update(overrides.pop("preprocessing", {}))
    return LoadedModel(
        artifact_id="art-2",
        tier=ModelTier.CLOUD,
        role=ModelRole.TEACHER,
        stage=TrainingStage.PRETRAIN,
        precision=TrainingPrecision.FP32,
        architecture="cnn_small",
        param_count=1,
        sparsity=Decimal("0.0"),
        storage_path="cloud/teacher/art-2.safetensors",
        signature="sig",
        signed_at=NOW,
        promoted=True,
        promoted_at=NOW,
        session_id="session-2",
        preprocessing=preprocessing,
        **overrides,
    )


def test_run_raises_when_both_sample_ids_set():
    seismic = _seismic()
    registry = _registry(True, _loaded_seismic(seismic), _StubModel(torch.zeros(4)))
    with patch(
        "integrations.inference.services.serving_waiter.model_registry", registry
    ):
        with pytest.raises(error, match="both"):
            InferenceServingWaiter.run(
                SEISMIC_KEY, np.zeros(100, dtype=np.float32), "ifg-1", "evt-1"
            )


def test_run_seismic_returns_argmax_class():
    seismic = _seismic()
    loaded = _loaded_seismic(seismic)
    model = _StubModel(torch.tensor([0.0, 0.0, 10.0, 0.0]))
    registry = _registry(True, loaded, model)
    with (
        patch(
            "integrations.inference.services.serving_waiter.model_registry",
            registry,
        ),
        patch(
            "integrations.inference.services.serving_waiter.InferencePersistService.select_seismic",
            return_value=seismic,
        ),
        patch(
            "integrations.inference.services.serving_waiter.Transformation.apply_seismic",
            return_value=np.zeros((1, 8, 16), dtype=np.float32),
        ),
    ):
        result, probabilities = InferenceServingWaiter.run(
            SEISMIC_KEY,
            np.zeros(100, dtype=np.float32),
            None,
            "evt-1",
        )
    assert isinstance(result, InferenceSeismic)
    assert result.abstained is False
    assert result.label is TrainingSeismicLabel.TR
    assert result.class_order == [
        TrainingSeismicLabel.VT,
        TrainingSeismicLabel.LP,
        TrainingSeismicLabel.TR,
        TrainingSeismicLabel.TC,
    ]
    assert probabilities["tr"] > probabilities["vt"]
    assert len(result.probabilities) == 4
    assert result.seismic_event_id == "evt-1"


def test_run_seismic_abstains_when_snr_rejected():
    seismic = _seismic()
    loaded = _loaded_seismic(seismic)
    registry = _registry(True, loaded, _StubModel(torch.zeros(4)))
    with (
        patch(
            "integrations.inference.services.serving_waiter.model_registry",
            registry,
        ),
        patch(
            "integrations.inference.services.serving_waiter.InferencePersistService.select_seismic",
            return_value=seismic,
        ),
        patch(
            "integrations.inference.services.serving_waiter.Transformation.apply_seismic",
            side_effect=TransformationRejected("snr below min"),
        ),
    ):
        result, probabilities = InferenceServingWaiter.run(
            SEISMIC_KEY,
            np.zeros(100, dtype=np.float32),
            None,
            "evt-1",
        )
    assert result.abstained is True
    assert result.abstained_reason is InferenceAbstainReason.LOW_SNR
    assert result.label is None
    assert probabilities == {}
    assert result.probabilities == []
