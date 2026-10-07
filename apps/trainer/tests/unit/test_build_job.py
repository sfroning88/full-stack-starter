"""
Author: Sean Froning
Created Date: 8.29.2026
Unit tests for trainer model builders
"""

from unittest.mock import MagicMock, patch

import pytest
import torch
from fiery_python import TrainingStage
from src.build_job import (
    DistillPair,
    SeismicCnn,
    _STUDENT_ARCHITECTURE,
    _TEACHER_ARCHITECTURE,
    _VIT_BASE_MODEL_ID,
    _VIT_REVISION,
    _VIT_SNAPSHOT,
    _VIT_WEIGHTS,
    _peft_targets,
    build_job,
)


def _lora(**overrides) -> dict:
    data = {
        "rank": 8,
        "alpha": 16,
        "dropout": 0.1,
        "epochs": 1,
        "learning_rate": 1e-4,
        "target_modules": {
            "query": True,
            "key": False,
            "value": False,
            "output": True,
        },
    }
    data.update(overrides)
    return data


def _lora_spec(**overrides) -> dict:
    data = {
        "stage": TrainingStage.LORA.value,
        "lora": _lora(),
        "base_model_id": _VIT_BASE_MODEL_ID,
        "revision": _VIT_REVISION,
    }
    data.update(overrides)
    return data


def _parent_spec(**overrides) -> dict:
    data = {
        "parent_storage_path": "edge/student/sess.safetensors",
        "parent_architecture": _TEACHER_ARCHITECTURE,
    }
    data.update(overrides)
    return data


def test_build_job_raises_when_stage_missing():
    with pytest.raises(RuntimeError, match="Missing stage from spec"):
        build_job({"stage": None})


def test_build_job_raises_when_stage_invalid():
    with pytest.raises(RuntimeError, match="Invalid stage from spec"):
        build_job({"stage": "unknown"})


def test_peft_targets_maps_qkv_and_proj():
    assert _peft_targets(
        {"query": True, "key": False, "value": False, "output": True}
    ) == ["qkv", "proj"]


def test_peft_targets_empty_when_all_false():
    assert (
        _peft_targets({"query": False, "key": False, "value": False, "output": False})
        == []
    )


def test_build_lora_job_raises_when_targets_empty():
    with pytest.raises(RuntimeError, match="Empty LoRA target modules"):
        build_job(
            _lora_spec(
                lora=_lora(
                    target_modules={
                        "query": False,
                        "key": False,
                        "value": False,
                        "output": False,
                    }
                )
            )
        )


def test_build_lora_job_raises_when_pin_missing():
    with pytest.raises(RuntimeError, match="Empty base_model_id"):
        build_job({"stage": TrainingStage.LORA.value, "lora": _lora()})


def test_build_lora_job_wraps_timm_backbone():
    backbone = MagicMock(name="backbone")
    wrapped = MagicMock(name="peft")
    with (
        patch(
            "src.build_job.hf_hub_download",
            return_value="/tmp/vit/model.safetensors",
        ) as download,
        patch("timm.create_model", return_value=backbone) as create_model,
        patch("peft.get_peft_model", return_value=wrapped) as get_peft_model,
    ):
        result = build_job(_lora_spec())
    assert result is wrapped
    download.assert_called_once_with(
        repo_id=_VIT_BASE_MODEL_ID,
        filename=_VIT_WEIGHTS,
        revision=_VIT_REVISION,
    )
    create_model.assert_called_once_with(
        _VIT_SNAPSHOT,
        pretrained=True,
        num_classes=2,
    )
    get_peft_model.assert_called_once()
    config = get_peft_model.call_args[0][1]
    assert config.r == 8
    assert config.lora_alpha == 16
    assert set(config.target_modules) == {"qkv", "proj"}
    assert list(config.modules_to_save) == ["head"]


def test_build_pretrain_job_returns_teacher_cnn():
    model = build_job({"stage": TrainingStage.PRETRAIN.value})
    assert isinstance(model, SeismicCnn)
    logits = model(torch.zeros(2, 1, 16, 16))
    assert logits.shape == (2, 4)


def test_build_job_unknown_architecture():
    with pytest.raises(RuntimeError, match="Unknown architecture"):
        build_job(
            {
                "stage": TrainingStage.PRUNE.value,
                "parent_storage_path": "path.safetensors",
                "parent_architecture": "missing",
            }
        )


def test_load_parent_requires_storage_path():
    with pytest.raises(RuntimeError, match="Missing parent_storage_path"):
        build_job(
            {
                "stage": TrainingStage.PRUNE.value,
                "parent_architecture": _STUDENT_ARCHITECTURE,
            }
        )


def test_build_distill_job_pairs_student_and_frozen_teacher():
    teacher = SeismicCnn(widths=(32, 64, 128))
    state = teacher.state_dict()
    with patch(
        "src.build_job.ModelStorageServices.load_artifact",
        return_value=(state, {}),
    ) as load:
        pair = build_job(
            {
                "stage": TrainingStage.DISTILL.value,
                "distill": {"student_architecture": _STUDENT_ARCHITECTURE},
                **_parent_spec(),
            }
        )
    load.assert_called_once_with("edge/student/sess.safetensors", is_weights=True)
    assert isinstance(pair, DistillPair)
    assert isinstance(pair.student, SeismicCnn)
    assert isinstance(pair.teacher, SeismicCnn)
    assert all(not param.requires_grad for param in pair.teacher.parameters())
    assert any(param.requires_grad for param in pair.student.parameters())
    logits = pair(torch.zeros(1, 1, 16, 16))
    assert logits.shape == (1, 4)


def test_build_prune_job_loads_parent():
    parent = SeismicCnn(widths=(16, 32, 64))
    with patch(
        "src.build_job.ModelStorageServices.load_artifact",
        return_value=(parent.state_dict(), {}),
    ):
        model = build_job(
            {
                "stage": TrainingStage.PRUNE.value,
                **_parent_spec(parent_architecture=_STUDENT_ARCHITECTURE),
            }
        )
    assert isinstance(model, SeismicCnn)
    for name, value in parent.state_dict().items():
        assert torch.equal(model.state_dict()[name], value)


def test_build_quantize_job_loads_parent():
    parent = SeismicCnn(widths=(16, 32, 64))
    with patch(
        "src.build_job.ModelStorageServices.load_artifact",
        return_value=(parent.state_dict(), {}),
    ):
        model = build_job(
            {
                "stage": TrainingStage.QUANTIZE.value,
                **_parent_spec(parent_architecture=_STUDENT_ARCHITECTURE),
            }
        )
    assert isinstance(model, SeismicCnn)
