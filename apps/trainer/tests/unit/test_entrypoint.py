"""
Author: Sean Froning
Created Date: 8.29.2026
Unit tests for trainer entrypoint
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import torch
from torch import nn
from fiery_python import (
    ModelMetric,
    ModelMetricName,
    ModelRole,
    ModelTier,
    TrainingPrecision,
    TrainingSplit,
    TrainingStage,
)
from src.build_job import DistillPair
from src.entrypoint import _VIT_PARAMS, _seed, entrypoint

_VIT_SNAPSHOT = "vit_small_patch16_224.augreg_in21k_ft_in1k"
_VIT_BASE_MODEL_ID = "timm/vit_small_patch16_224.augreg_in21k_ft_in1k"
_VIT_REVISION = "7e2c55630205e1266030f18370f4c6ed1a514b52"


class _TinyModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.weight = nn.Parameter(torch.ones(2))

    def to(self, _device: str) -> "_TinyModel":
        return self

    def cpu(self) -> "_TinyModel":
        return self


def _metrics() -> list[ModelMetric]:
    return [
        ModelMetric(
            name=ModelMetricName.RECALL,
            split=TrainingSplit.TEST,
            value=Decimal("1.0"),
            artifact_id="art-1",
        )
    ]


def _decision() -> dict:
    return {
        "threshold": 0.5,
        "abstention_band": "0.00000",
        "transform_hash": "a" * 64,
        "op_version": 1,
    }


def _spec(**overrides) -> dict:
    data = {
        "session_id": "sess-1",
        "stage": TrainingStage.LORA.value,
        "tier": ModelTier.CLOUD.value,
        "role": ModelRole.SCREENER.value,
        "precision": TrainingPrecision.FP32.value,
        "seed": 42,
        "lora": {"epochs": 1, "learning_rate": 1e-4},
        "base_model_id": _VIT_BASE_MODEL_ID,
        "revision": _VIT_REVISION,
        "callback_url": "https://ai.example/api/callback/train",
        "storage_path": "unused",
    }
    data.update(overrides)
    return data


def test_seed_sets_torch_rng():
    _seed(0)
    first = torch.rand(1)
    _seed(0)
    second = torch.rand(1)
    assert torch.equal(first, second)


def test_entrypoint_saves_then_callbacks():
    metrics = _metrics()
    decision = _decision()
    model = _TinyModel()
    loaders = {"train": object()}
    spec = _spec()
    adapter = {"lora_A": torch.ones(2)}
    with (
        patch("src.entrypoint.build_loaders", return_value=loaders),
        patch("src.entrypoint.build_job", return_value=model),
        patch("src.entrypoint.train_model", return_value=model),
        patch("src.entrypoint.score_model", return_value=(metrics, decision)),
        patch(
            "peft.get_peft_model_state_dict",
            return_value=adapter,
        ) as adapter_dict,
        patch("src.entrypoint.ModelStorageServices.save_artifact") as save,
        patch(
            "src.entrypoint.ModelStorageServices.head_hmac",
            return_value="b" * 64,
        ),
        patch(
            "src.entrypoint.save_checkpoint", side_effect=lambda *a, **k: k["sidecar"]
        ),
        patch("src.entrypoint.send_callback") as callback,
    ):
        result = entrypoint(spec, _VIT_SNAPSHOT)
    save.assert_called_once()
    weights_key = save.call_args[0][2]
    sidecar = save.call_args[0][1]
    assert save.call_args[0][0] is adapter
    adapter_dict.assert_called_once()
    assert weights_key == "cloud/screener/sess-1.safetensors"
    assert sidecar["architecture"] == _VIT_SNAPSHOT
    assert sidecar["decision"] is decision
    assert sidecar["lora"] == spec["lora"]
    assert sidecar["base_model_id"] == _VIT_BASE_MODEL_ID
    assert sidecar["revision"] == _VIT_REVISION
    callback.assert_called_once()
    kwargs = callback.call_args.kwargs
    assert kwargs["storage_path"] == "cloud/screener/sess-1.safetensors"
    assert kwargs["signature"] == "b" * 64
    assert kwargs["architecture"] == _VIT_SNAPSHOT
    assert kwargs["param_count"] == _VIT_PARAMS + 2
    assert kwargs["metrics"] is metrics
    assert kwargs["decision"] is decision
    assert result == {
        "ok": True,
        "spec": "sess-1",
        "storage_path": "cloud/screener/sess-1.safetensors",
    }


def test_entrypoint_skips_callback_when_train_fails():
    spec = _spec()
    with (
        patch(
            "src.entrypoint.build_loaders",
            side_effect=RuntimeError("Failed to load dataset"),
        ),
        patch("src.entrypoint.send_callback") as callback,
    ):
        result = entrypoint(spec, _VIT_SNAPSHOT)
    callback.assert_not_called()
    assert result == {
        "ok": False,
        "spec": "sess-1",
    }


def test_entrypoint_saves_distilled_student_only():
    student = _TinyModel()
    teacher = _TinyModel()
    pair = DistillPair(student=student, teacher=teacher)
    pair.to = lambda _device: pair
    spec = _spec(
        stage=TrainingStage.DISTILL.value,
        tier=ModelTier.EDGE.value,
        role=ModelRole.STUDENT.value,
        distill={"student_architecture": "cnn_tiny"},
    )
    spec.pop("lora")
    with (
        patch("src.entrypoint.build_loaders", return_value={"train": object()}),
        patch("src.entrypoint.build_job", return_value=pair),
        patch("src.entrypoint.train_model", return_value=pair),
        patch("src.entrypoint.score_model", return_value=(_metrics(), _decision())),
        patch("src.entrypoint.ModelStorageServices.save_artifact") as save,
        patch(
            "src.entrypoint.ModelStorageServices.head_hmac",
            return_value="b" * 64,
        ),
        patch(
            "src.entrypoint.save_checkpoint", side_effect=lambda *a, **k: k["sidecar"]
        ),
        patch("src.entrypoint.send_callback") as callback,
    ):
        entrypoint(spec, "cnn_tiny")
    state_dict = save.call_args[0][0]
    sidecar = save.call_args[0][1]
    assert "weight" in state_dict
    assert not any(key.startswith("student.") for key in state_dict)
    assert not any(key.startswith("teacher.") for key in state_dict)
    assert sidecar["architecture"] == "cnn_tiny"
    assert "lora" not in sidecar
    assert callback.call_args.kwargs["architecture"] == "cnn_tiny"
    assert callback.call_args.kwargs["param_count"] == student.weight.numel()


def test_entrypoint_persists_quantize_example_shape():
    model = _TinyModel()
    spec = _spec(
        stage=TrainingStage.QUANTIZE.value,
        tier=ModelTier.EDGE.value,
        role=ModelRole.STUDENT.value,
        precision=TrainingPrecision.INT8.value,
        quantize={"method": "ptq"},
        example_shape=[1, 1, 16, 16],
    )
    spec.pop("lora")
    with (
        patch("src.entrypoint.build_loaders", return_value={"train": object()}),
        patch("src.entrypoint.build_job", return_value=model),
        patch("src.entrypoint.train_model", return_value=model),
        patch("src.entrypoint.score_model", return_value=(_metrics(), _decision())),
        patch("src.entrypoint.ModelStorageServices.save_artifact") as save,
        patch(
            "src.entrypoint.ModelStorageServices.head_hmac",
            return_value="b" * 64,
        ),
        patch(
            "src.entrypoint.save_checkpoint", side_effect=lambda *a, **k: k["sidecar"]
        ),
        patch("src.entrypoint.send_callback"),
        patch("torch.export.export", return_value=MagicMock()) as export,
        patch("torch.export.save", side_effect=lambda _ep, buf: buf.write(b"pt2")),
    ):
        entrypoint(spec, "cnn_tiny")
    export.assert_called_once()
    payload = save.call_args[0][0]
    sidecar = save.call_args[0][1]
    assert payload == b"pt2"
    assert sidecar["example_shape"] == [1, 1, 16, 16]
    assert sidecar["spec"]["example_shape"] == [1, 1, 16, 16]
    assert sidecar["stage"] == TrainingStage.QUANTIZE.value


def test_entrypoint_scores_and_saves_rebound_model():
    original = _TinyModel()
    converted = _TinyModel()
    converted.weight.data.fill_(3.0)
    spec = _spec()
    with (
        patch("src.entrypoint.build_loaders", return_value={"train": object()}),
        patch("src.entrypoint.build_job", return_value=original),
        patch("src.entrypoint.train_model", return_value=converted),
        patch(
            "src.entrypoint.score_model", return_value=(_metrics(), _decision())
        ) as score,
        patch(
            "peft.get_peft_model_state_dict",
            return_value={"weight": converted.weight},
        ),
        patch("src.entrypoint.ModelStorageServices.save_artifact") as save,
        patch(
            "src.entrypoint.ModelStorageServices.head_hmac",
            return_value="b" * 64,
        ),
        patch(
            "src.entrypoint.save_checkpoint", side_effect=lambda *a, **k: k["sidecar"]
        ),
        patch("src.entrypoint.send_callback"),
    ):
        entrypoint(spec, _VIT_SNAPSHOT)
    assert score.call_args[0][1] is converted
    assert save.call_args[0][0]["weight"].tolist() == [3.0, 3.0]
