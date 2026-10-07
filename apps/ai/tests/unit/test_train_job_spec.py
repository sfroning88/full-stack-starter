"""
Author: Sean Froning
Created Date: 8.23.2026
Unit tests for TrainJobSpec
"""

import pytest
from datetime import datetime, timezone
from fiery_python import (
    DatasetVersion,
    ModelArtifact,
    ModelRole,
    ModelTier,
    TrainingHyperparameterDistill,
    TrainingHyperparameterLora,
    TrainingHyperparameterPretrain,
    TrainingHyperparameterPrune,
    TrainingHyperparameterQuantize,
    TrainingPrecision,
    TrainingSession,
    TrainingSignal,
    TrainingStage,
    TrainingStatus,
    TrainingTargetModules,
)
from fiery_python.fastapi.error import error as AppError
from integrations.train.services.job_spec import (
    TrainJobSpec,
    _VIT_BASE_MODEL_ID,
    _VIT_REVISION,
)


def _session(**overrides) -> TrainingSession:
    payload = {
        "id": "sess-1",
        "signal": TrainingSignal.DEFORMATION,
        "stage": TrainingStage.LORA,
        "status": TrainingStatus.PENDING,
        "samples": 10,
        "seed": 42,
        "git_sha": "abc123",
        "contract_id": "contract-1",
        "version_id": "ver-1",
    }
    payload.update(overrides)
    return TrainingSession(**payload)


def _version() -> DatasetVersion:
    return DatasetVersion(
        id="ver-1",
        transform_hash="abc",
        manifest_path="contract-1/abc/manifest.json",
        shard_count=2,
        sample_count=10,
        status=TrainingStatus.COMPLETED,
        contract_id="contract-1",
    )


def _pretrain() -> TrainingHyperparameterPretrain:
    return TrainingHyperparameterPretrain(id="pretrain-1")


def _lora() -> TrainingHyperparameterLora:
    return TrainingHyperparameterLora(id="lora-1", target_modules_id="mod-1")


def _modules() -> TrainingTargetModules:
    return TrainingTargetModules(id="mod-1")


def _distill() -> TrainingHyperparameterDistill:
    return TrainingHyperparameterDistill(
        id="distill-1", student_architecture="seismic_cnn_student"
    )


def _prune() -> TrainingHyperparameterPrune:
    return TrainingHyperparameterPrune(id="prune-1")


def _quantize() -> TrainingHyperparameterQuantize:
    return TrainingHyperparameterQuantize(id="quantize-1")


def _parent() -> ModelArtifact:
    return ModelArtifact(
        id="parent-1",
        tier=ModelTier.CLOUD,
        role=ModelRole.TEACHER,
        stage=TrainingStage.PRETRAIN,
        precision=TrainingPrecision.FP32,
        architecture="seismic_cnn_teacher",
        param_count=1,
        storage_path="cloud/teacher/sess.safetensors",
        signature="sig",
        signed_at=datetime.now(timezone.utc),
        session_id="teacher-sess",
    )


def _parent_id(stage: TrainingStage) -> str | None:
    if stage in (
        TrainingStage.DISTILL,
        TrainingStage.PRUNE,
        TrainingStage.QUANTIZE,
    ):
        return "parent-1"
    return None


def _packed(stage: TrainingStage):
    if stage is TrainingStage.PRETRAIN:
        return (_pretrain(), None, None, None, None)
    if stage is TrainingStage.LORA:
        return (None, (_lora(), _modules()), None, None, None)
    if stage is TrainingStage.DISTILL:
        return (None, None, _distill(), None, None)
    if stage is TrainingStage.PRUNE:
        return (None, None, None, _prune(), None)
    return (None, None, None, None, _quantize())


@pytest.mark.parametrize(
    "stage,signal,blob_key,tier,role,precision",
    [
        (
            TrainingStage.PRETRAIN,
            TrainingSignal.SEISMIC,
            "pretrain",
            ModelTier.CLOUD,
            ModelRole.TEACHER,
            TrainingPrecision.FP32,
        ),
        (
            TrainingStage.LORA,
            TrainingSignal.DEFORMATION,
            "lora",
            ModelTier.CLOUD,
            ModelRole.SCREENER,
            TrainingPrecision.FP32,
        ),
        (
            TrainingStage.DISTILL,
            TrainingSignal.SEISMIC,
            "distill",
            ModelTier.EDGE,
            ModelRole.STUDENT,
            TrainingPrecision.FP32,
        ),
        (
            TrainingStage.PRUNE,
            TrainingSignal.SEISMIC,
            "prune",
            ModelTier.EDGE,
            ModelRole.STUDENT,
            TrainingPrecision.FP32,
        ),
        (
            TrainingStage.QUANTIZE,
            TrainingSignal.SEISMIC,
            "quantize",
            ModelTier.EDGE,
            ModelRole.STUDENT,
            TrainingPrecision.INT8,
        ),
    ],
)
def test_build_job_spec_payload(
    monkeypatch, stage, signal, blob_key, tier, role, precision
):
    monkeypatch.setattr(
        "integrations.train.services.job_spec.config.get_required",
        lambda _key: "https://ai.example",
    )
    monkeypatch.setattr(
        "integrations.train.services.job_spec.TrainPersistService.select_artifact",
        lambda _artifact_id: _parent(),
    )
    spec = TrainJobSpec.build_job_spec(
        _session(stage=stage, signal=signal),
        _version(),
        _packed(stage),
        "nonce-1",
        _parent_id(stage),
    )
    assert spec["session_id"] == "sess-1"
    assert spec["signal"] == signal.value
    assert spec["stage"] == stage.value
    assert spec["shard_prefix"] == "contract-1/abc/"
    assert spec["manifest_path"] == "contract-1/abc/manifest.json"
    assert spec["callback_url"] == "https://ai.example/api/callback/train"
    assert spec["nonce"] == "nonce-1"
    assert spec["tier"] == tier.value
    assert spec["role"] == role.value
    assert spec["precision"] == precision.value
    assert blob_key in spec
    assert spec[blob_key]["id"] == f"{blob_key}-1"
    if _parent_id(stage):
        assert spec["parent_id"] == "parent-1"
        assert spec["parent_storage_path"] == "cloud/teacher/sess.safetensors"
        assert spec["parent_architecture"] == "seismic_cnn_teacher"
        assert spec["parent_precision"] == TrainingPrecision.FP32.value
    else:
        assert "parent_id" not in spec
    if stage is TrainingStage.LORA:
        assert spec["base_model_id"] == _VIT_BASE_MODEL_ID
        assert spec["revision"] == _VIT_REVISION
    else:
        assert "base_model_id" not in spec
        assert "revision" not in spec


def test_build_job_spec_lora_target_modules(monkeypatch):
    monkeypatch.setattr(
        "integrations.train.services.job_spec.config.get_required",
        lambda _key: "https://ai.example",
    )
    spec = TrainJobSpec.build_job_spec(
        _session(), _version(), _packed(TrainingStage.LORA), "nonce-1"
    )
    assert spec["lora"]["target_modules"]["query"] is True
    assert spec["lora"]["target_modules"]["key"] is False


def test_build_job_spec_returns_none_when_parent_missing(monkeypatch):
    monkeypatch.setattr(
        "integrations.train.services.job_spec.config.get_required",
        lambda _key: "https://ai.example",
    )
    spec = TrainJobSpec.build_job_spec(
        _session(stage=TrainingStage.DISTILL, signal=TrainingSignal.SEISMIC),
        _version(),
        _packed(TrainingStage.DISTILL),
        "nonce-1",
    )
    assert spec is None


def test_build_job_spec_returns_none_when_stage_slot_empty(monkeypatch):
    monkeypatch.setattr(
        "integrations.train.services.job_spec.config.get_required",
        lambda _key: "https://ai.example",
    )
    spec = TrainJobSpec.build_job_spec(
        _session(stage=TrainingStage.LORA),
        _version(),
        (_pretrain(), None, None, None, None),
        "nonce-1",
    )
    assert spec is None


def test_build_job_spec_requires_api_url(monkeypatch):
    monkeypatch.setattr(
        "integrations.train.services.job_spec.config.get_required",
        lambda _key: None,
    )
    with pytest.raises(AppError, match="AI_API_URL"):
        TrainJobSpec.build_job_spec(
            _session(), _version(), _packed(TrainingStage.LORA), "nonce-1"
        )
