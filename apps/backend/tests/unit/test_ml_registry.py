"""
Author: Sean Froning
Created Date: 8.29.2026
Unit tests for the inference-side model registry cache
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fiery_python import ModelRole, ModelTier, TrainingPrecision, TrainingStage
from ml.models import LoadedModel
from ml.registry import (
    SeismicCnn,
    _ModelRegistry,
    _VIT_BASE_MODEL_ID,
    _VIT_REVISION,
    _VIT_SNAPSHOT,
    _VIT_WEIGHTS,
)

KEY = (ModelTier.CLOUD, ModelRole.SCREENER)
NOW = datetime.now(tz=timezone.utc)


def _artifact_row(**overrides):
    row = {
        "id": "art-1",
        "tier": ModelTier.CLOUD.value,
        "role": ModelRole.SCREENER.value,
        "stage": TrainingStage.LORA.value,
        "precision": TrainingPrecision.FP32.value,
        "architecture": _VIT_SNAPSHOT,
        "param_count": 22_100_000,
        "sparsity": "0.0",
        "storage_path": "cloud/screener/art-1.safetensors",
        "signature": "sig-art-1",
        "signed_at": NOW,
        "promoted": True,
        "promoted_at": NOW,
        "session_id": "session-1",
        "parent_id": None,
    }
    row.update(overrides)
    return row


def _loaded(artifact_id: str = "art-1") -> LoadedModel:
    return LoadedModel(
        artifact_id=artifact_id,
        tier=ModelTier.CLOUD,
        role=ModelRole.SCREENER,
        stage=TrainingStage.LORA,
        precision=TrainingPrecision.FP32,
        architecture=_VIT_SNAPSHOT,
        param_count=22_100_000,
        sparsity=Decimal("0.0"),
        storage_path="cloud/screener/art-1.safetensors",
        signature="sig-art-1",
        signed_at=NOW,
        promoted=True,
        promoted_at=NOW,
        session_id="session-1",
    )


def test_get_raises_when_slot_empty():
    registry = _ModelRegistry()

    with pytest.raises(RuntimeError, match="not loaded"):
        registry.get(KEY)


def test_get_metadata_returns_empty_when_slot_empty():
    registry = _ModelRegistry()

    assert registry.get_metadata(KEY) == {}


def test_is_ready_false_when_slot_empty():
    registry = _ModelRegistry()

    assert registry.is_ready(KEY) is False


def test_load_resets_slot_when_no_promoted_row():
    registry = _ModelRegistry()
    slot = registry._slot(KEY)
    slot.get().model = object()
    slot.get().artifact_id = "stale"

    with patch.object(registry, "_fetch_promoted_artifact", return_value=None):
        registry.load(KEY)

    assert registry.is_ready(KEY) is False
    assert registry.get_metadata(KEY) == {}


def test_load_resets_slot_when_row_has_no_id():
    registry = _ModelRegistry()
    slot = registry._slot(KEY)
    slot.get().model = object()
    slot.get().artifact_id = "stale"

    with patch.object(registry, "_fetch_promoted_artifact", return_value={"id": None}):
        registry.load(KEY)

    assert registry.is_ready(KEY) is False
    assert registry.get_metadata(KEY) == {}


def test_load_wraps_lookup_failure():
    registry = _ModelRegistry()

    with patch.object(
        registry, "_fetch_promoted_artifact", side_effect=RuntimeError("db down")
    ):
        with pytest.raises(RuntimeError, match="Model registry lookup failed"):
            registry.load(KEY)


def test_load_skips_when_already_current():
    registry = _ModelRegistry()
    slot = registry._slot(KEY)
    slot.get().model = object()
    slot.get().metadata = _loaded()
    slot.get().artifact_id = "art-1"

    with (
        patch.object(
            registry, "_fetch_promoted_artifact", return_value=_artifact_row()
        ),
        patch.object(registry, "_load_model_entry") as load_entry,
    ):
        registry.load(KEY)

    load_entry.assert_not_called()


def test_load_reloads_when_force_even_if_current():
    registry = _ModelRegistry()
    slot = registry._slot(KEY)
    slot.get().model = object()
    slot.get().metadata = _loaded()
    slot.get().artifact_id = "art-1"
    artifact = object()
    entry = _loaded()

    with (
        patch.object(
            registry, "_fetch_promoted_artifact", return_value=_artifact_row()
        ),
        patch.object(
            registry, "_load_model_entry", return_value=(entry, artifact)
        ) as load_entry,
    ):
        registry.load(KEY, force=True)

    load_entry.assert_called_once()
    assert registry.get(KEY) is artifact
    assert registry.get_metadata(KEY)["artifact_id"] == "art-1"
    assert registry.is_ready(KEY) is True


def test_load_keeps_empty_slot_when_artifact_fails_to_materialize():
    registry = _ModelRegistry()

    with (
        patch.object(
            registry, "_fetch_promoted_artifact", return_value=_artifact_row()
        ),
        patch.object(registry, "_load_model_entry", return_value=(None, None)),
    ):
        with pytest.raises(RuntimeError, match="failed to materialize"):
            registry.load(KEY)

    assert registry.is_ready(KEY) is False


def test_load_keeps_cached_when_artifact_fails_to_materialize():
    registry = _ModelRegistry()
    cached = object()
    slot = registry._slot(KEY)
    slot.get().model = cached
    slot.get().metadata = _loaded("stale")
    slot.get().artifact_id = "stale"

    with (
        patch.object(
            registry, "_fetch_promoted_artifact", return_value=_artifact_row()
        ),
        patch.object(registry, "_load_model_entry", return_value=(None, None)),
    ):
        with pytest.raises(RuntimeError, match="failed to materialize"):
            registry.load(KEY)

    assert registry.get(KEY) is cached
    assert registry.get_metadata(KEY)["artifact_id"] == "stale"


def test_load_caches_model_and_metadata():
    registry = _ModelRegistry()
    artifact = object()
    entry = _loaded()

    with (
        patch.object(
            registry, "_fetch_promoted_artifact", return_value=_artifact_row()
        ),
        patch.object(registry, "_load_model_entry", return_value=(entry, artifact)),
    ):
        registry.load(KEY)

    assert registry.get(KEY) is artifact
    metadata = registry.get_metadata(KEY)
    assert metadata["tier"] == ModelTier.CLOUD
    assert metadata["role"] == ModelRole.SCREENER
    assert metadata["architecture"] == _VIT_SNAPSHOT
    assert metadata["storage_path"] == "cloud/screener/art-1.safetensors"
    assert metadata["signature"] == "sig-art-1"
    assert metadata["promoted"] is True
    assert metadata["session_id"] == "session-1"


def test_reset_drops_all_cached_slots():
    registry = _ModelRegistry()
    other = (ModelTier.EDGE, ModelRole.STUDENT)
    registry._slot(KEY).get().model = object()
    registry._slot(other).get().model = object()

    registry.reset()

    assert registry.is_ready(KEY) is False
    assert registry.is_ready(other) is False


def test_load_model_entry_returns_none_without_storage_path():
    registry = _ModelRegistry()

    entry, artifact = registry._load_model_entry({"id": "art-1"}, "art-1")

    assert entry is None
    assert artifact is None


def test_load_model_entry_returns_none_when_storage_load_fails():
    registry = _ModelRegistry()

    with patch(
        "ml.registry.ModelStorageServices.load_artifact",
        side_effect=RuntimeError("s3 unavailable"),
    ):
        entry, artifact = registry._load_model_entry(_artifact_row(), "art-1")

    assert entry is None
    assert artifact is None


def test_load_model_entry_returns_none_when_materialize_fails():
    registry = _ModelRegistry()
    state_dict = {"weight": object()}
    sidecar = {"lora": {"rank": 8, "alpha": 16, "dropout": 0.1, "target_modules": {}}}

    with (
        patch(
            "ml.registry.ModelStorageServices.load_artifact",
            return_value=(state_dict, sidecar),
        ),
        patch.object(
            registry,
            "materialize",
            side_effect=RuntimeError("sidecar missing lora"),
        ),
    ):
        entry, artifact = registry._load_model_entry(_artifact_row(), "art-1")

    assert entry is None
    assert artifact is None


def test_load_model_entry_builds_loaded_model():
    registry = _ModelRegistry()
    artifact = MagicMock(name="weights")
    row = _artifact_row(parent_id="parent-9")
    state_dict = {"lora_A": object()}
    sidecar = {
        "architecture": _VIT_SNAPSHOT,
        "stage": TrainingStage.LORA.value,
        "base_model_id": _VIT_BASE_MODEL_ID,
        "revision": _VIT_REVISION,
        "lora": {
            "rank": 8,
            "alpha": 16,
            "dropout": 0.1,
            "target_modules": {"query": True, "output": True},
        },
        "decision": {
            "threshold": 0.5,
            "abstention_band": "0.00000",
            "transform_hash": "a" * 64,
            "op_version": 1,
        },
    }

    with (
        patch(
            "ml.registry.ModelStorageServices.load_artifact",
            return_value=(state_dict, sidecar),
        ),
        patch.object(registry, "materialize", return_value=artifact),
        patch("ml.registry.set_peft_model_state_dict") as set_adapter,
    ):
        entry, loaded = registry._load_model_entry(row, "art-1")

    set_adapter.assert_called_once_with(artifact, state_dict)
    artifact.load_state_dict.assert_not_called()
    artifact.eval.assert_called_once()
    assert loaded is artifact
    assert entry is not None
    assert entry.artifact_id == "art-1"
    assert entry.parent_id == "parent-9"
    assert entry.param_count == 22_100_000
    assert entry.sparsity == Decimal("0.0")
    assert entry.storage_path == "cloud/screener/art-1.safetensors"
    assert entry.signature == "sig-art-1"
    assert entry.signed_at == NOW
    assert entry.promoted is True
    assert entry.session_id == "session-1"
    assert entry.preprocessing["threshold"] == 0.5


def test_materialize_vit_delegates_to_screener():
    sidecar = {
        "stage": TrainingStage.LORA.value,
        "architecture": _VIT_SNAPSHOT,
        "lora": {
            "rank": 8,
            "alpha": 16,
            "dropout": 0.1,
            "target_modules": {"query": True},
        },
    }
    stub = MagicMock(name="vit")
    with patch.object(
        _ModelRegistry, "_materialize_screener", return_value=stub
    ) as screener:
        assert _ModelRegistry.materialize(sidecar) is stub
    screener.assert_called_once_with(sidecar)


def test_materialize_cnn_pretrain_and_distill():
    small = _ModelRegistry.materialize({"stage": TrainingStage.PRETRAIN.value})
    tiny = _ModelRegistry.materialize({"stage": TrainingStage.DISTILL.value})
    assert isinstance(small, SeismicCnn)
    assert isinstance(tiny, SeismicCnn)


def test_materialize_cnn_delegates_with_stage():
    sidecar = {"stage": TrainingStage.PRETRAIN.value}
    with patch.object(
        _ModelRegistry, "_materialize_cnn", return_value=MagicMock()
    ) as cnn:
        _ModelRegistry.materialize(sidecar)
    cnn.assert_called_once_with(TrainingStage.PRETRAIN)


def test_load_model_entry_loads_exported_quantize_without_eval():
    registry = _ModelRegistry()
    exported_module = MagicMock(name="exported_module")
    exported = MagicMock(name="exported")
    exported.module.return_value = exported_module
    payload = b"pt2-bytes"
    sidecar = {
        "stage": TrainingStage.QUANTIZE.value,
        "decision": {
            "threshold": 0.5,
            "abstention_band": "0.00000",
            "transform_hash": "a" * 64,
            "op_version": 1,
        },
    }
    row = _artifact_row(
        tier=ModelTier.EDGE.value,
        role=ModelRole.STUDENT.value,
        stage=TrainingStage.QUANTIZE.value,
        architecture="cnn_tiny",
        storage_path="edge/student/art-1.safetensors",
    )
    with (
        patch(
            "ml.registry.ModelStorageServices.load_artifact",
            return_value=(payload, sidecar),
        ),
        patch.object(registry, "materialize") as materialize,
        patch("ml.registry.torch.export.load", return_value=exported) as load_export,
    ):
        entry, loaded = registry._load_model_entry(row, "art-1")
    materialize.assert_not_called()
    load_export.assert_called_once()
    exported_module.eval.assert_not_called()
    assert loaded is exported_module
    assert entry is not None
    assert entry.stage is TrainingStage.QUANTIZE


def test_materialize_requires_stage():
    with pytest.raises(RuntimeError, match="Stage from sidecar missing or malformed"):
        _ModelRegistry.materialize({"architecture": "resnet18"})


def test_materialize_screener_requires_lora():
    with pytest.raises(RuntimeError, match="sidecar missing lora"):
        _ModelRegistry._materialize_screener({"architecture": _VIT_SNAPSHOT})


def test_materialize_screener_requires_target_modules():
    with pytest.raises(RuntimeError, match="Empty LoRA"):
        _ModelRegistry._materialize_screener(
            {
                "architecture": _VIT_SNAPSHOT,
                "lora": {
                    "rank": 8,
                    "alpha": 16,
                    "dropout": 0.1,
                    "target_modules": {},
                },
            }
        )


def test_materialize_screener_requires_base_pin():
    with pytest.raises(RuntimeError, match="Empty base_model_id"):
        _ModelRegistry._materialize_screener(
            {
                "architecture": _VIT_SNAPSHOT,
                "lora": {
                    "rank": 8,
                    "alpha": 16,
                    "dropout": 0.1,
                    "target_modules": {"query": True},
                },
            }
        )


def test_materialize_screener_wraps_pinned_backbone():
    backbone = MagicMock(name="backbone")
    wrapped = MagicMock(name="peft")
    sidecar = {
        "architecture": _VIT_SNAPSHOT,
        "base_model_id": _VIT_BASE_MODEL_ID,
        "revision": _VIT_REVISION,
        "lora": {
            "rank": 8,
            "alpha": 16,
            "dropout": 0.1,
            "target_modules": {"query": True, "output": True},
        },
    }
    with (
        patch(
            "ml.registry.hf_hub_download",
            return_value="/tmp/vit/model.safetensors",
        ) as download,
        patch("ml.registry.timm.create_model", return_value=backbone) as create_model,
        patch("ml.registry.load_checkpoint") as load_checkpoint,
        patch("ml.registry.get_peft_model", return_value=wrapped) as get_peft_model,
    ):
        result = _ModelRegistry._materialize_screener(sidecar)
    assert result is wrapped
    download.assert_called_once_with(
        repo_id=_VIT_BASE_MODEL_ID,
        filename=_VIT_WEIGHTS,
        revision=_VIT_REVISION,
        local_files_only=True,
    )
    create_model.assert_called_once_with(
        _VIT_SNAPSHOT,
        pretrained=False,
        num_classes=1000,
    )
    load_checkpoint.assert_called_once_with(
        backbone,
        "/tmp/vit/model.safetensors",
        strict=False,
    )
    backbone.reset_classifier.assert_called_once_with(num_classes=2)
    config = get_peft_model.call_args[0][1]
    assert config.modules_to_save == ["head"]
    assert set(config.target_modules) == {"qkv", "proj"}
