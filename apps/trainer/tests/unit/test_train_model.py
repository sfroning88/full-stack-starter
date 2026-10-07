"""
Author: Sean Froning
Created Date: 8.27.2026
Unit tests for trainer training loop
"""

import importlib.util
from unittest.mock import MagicMock, patch

import pytest
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
from fiery_python import (
    TrainingOptimizer,
    TrainingPruningCriterion,
    TrainingQuantizeMethod,
    TrainingRateSchedule,
    TrainingSparsitySchedule,
    TrainingStage,
)
from src.build_job import DistillPair, SeismicCnn
from src.train_model import (
    _class_weights,
    _sparsity_at,
    _train_distill_model,
    _train_lora_model,
    _train_pretrain_model,
    _train_prune_model,
    train_model,
)


def _linear_loader() -> DataLoader:
    features = torch.randn(4, 4)
    targets = torch.tensor([0, 1, 2, 3])
    return DataLoader(TensorDataset(features, targets), batch_size=4)


def _cnn_loader() -> DataLoader:
    features = torch.randn(4, 1, 16, 16)
    targets = torch.tensor([0, 1, 2, 3])
    return DataLoader(TensorDataset(features, targets), batch_size=2)


def test_train_model_raises_when_stage_missing():
    with pytest.raises(RuntimeError, match="Missing stage from spec"):
        train_model(nn.Linear(4, 4), {"train": _linear_loader()}, {"stage": None})


def test_train_model_raises_when_stage_invalid():
    with pytest.raises(RuntimeError, match="Invalid stage from spec"):
        train_model(nn.Linear(4, 4), {"train": _linear_loader()}, {"stage": "unknown"})


@pytest.mark.parametrize(
    "stage,builder",
    [
        (TrainingStage.PRETRAIN.value, "_train_pretrain_model"),
        (TrainingStage.LORA.value, "_train_lora_model"),
        (TrainingStage.DISTILL.value, "_train_distill_model"),
        (TrainingStage.PRUNE.value, "_train_prune_model"),
        (TrainingStage.QUANTIZE.value, "_train_quantize_model"),
    ],
)
def test_train_model_dispatches_stage(stage: str, builder: str):
    model = nn.Linear(4, 4)
    loaders = {"train": _linear_loader()}
    spec = {"stage": stage}
    with patch(f"src.train_model.{builder}") as train:
        train.return_value = model
        result = train_model(model, loaders, spec)
    train.assert_called_once_with(model, loaders, spec)
    assert result is model


def test_train_lora_model_runs_one_step():
    model = nn.Linear(4, 4)
    loaders = {"train": _linear_loader()}
    before = model.weight.detach().clone()
    trained = _train_lora_model(
        model,
        loaders,
        {
            "stage": TrainingStage.LORA.value,
            "lora": {"epochs": 1, "learning_rate": 1e-2},
        },
    )
    assert trained is model
    assert not torch.equal(before, model.weight.detach())


def test_train_pretrain_model_runs_one_epoch():
    model = nn.Linear(4, 4)
    before = model.weight.detach().clone()
    _train_pretrain_model(
        model,
        {"train": _linear_loader()},
        {
            "pretrain": {
                "epochs": 1,
                "optimizer": TrainingOptimizer.ADAMW.value,
                "learning_rate": 1e-2,
                "weight_decay": "0.01",
                "lr_schedule": TrainingRateSchedule.CONSTANT.value,
            }
        },
    )
    assert not torch.equal(before, model.weight.detach())


def test_train_distill_model_updates_student_only():
    student = nn.Linear(4, 4)
    teacher = nn.Linear(4, 4)
    for param in teacher.parameters():
        param.requires_grad = False
    pair = DistillPair(student=student, teacher=teacher)
    student_before = student.weight.detach().clone()
    teacher_before = teacher.weight.detach().clone()
    _train_distill_model(
        pair,
        {"train": _linear_loader()},
        {
            "distill": {
                "temperature": 2.0,
                "alpha": "0.7",
                "epochs": 1,
                "learning_rate": 1e-2,
            }
        },
    )
    assert not torch.equal(student_before, student.weight.detach())
    assert torch.equal(teacher_before, teacher.weight.detach())


def test_train_prune_model_sparsifies_and_removes_masks():
    model = SeismicCnn(widths=(8, 16))
    zeros_before = sum(
        int((module.weight == 0).sum())
        for module in model.modules()
        if isinstance(module, nn.Conv2d)
    )
    _train_prune_model(
        model,
        {"train": _cnn_loader()},
        {
            "prune": {
                "target_sparsity": "0.5",
                "iterations": 1,
                "finetune_epochs_per_iter": 1,
                "sparsity_schedule": TrainingSparsitySchedule.ONE_SHOT.value,
                "pruning_criterion": TrainingPruningCriterion.L1_MAGNITUDE.value,
            }
        },
    )
    zeros_after = sum(
        int((module.weight == 0).sum())
        for module in model.modules()
        if isinstance(module, nn.Conv2d)
    )
    assert zeros_after > zeros_before
    assert not any(
        hasattr(module, "weight_mask")
        for module in model.modules()
        if isinstance(module, nn.Conv2d)
    )


def test_train_prune_model_raises_without_convs():
    with pytest.raises(RuntimeError, match="No Conv2d modules to prune"):
        _train_prune_model(
            nn.Linear(4, 4),
            {"train": _linear_loader()},
            {
                "prune": {
                    "target_sparsity": "0.5",
                    "iterations": 1,
                    "finetune_epochs_per_iter": 1,
                    "sparsity_schedule": TrainingSparsitySchedule.ONE_SHOT.value,
                    "pruning_criterion": TrainingPruningCriterion.L1_MAGNITUDE.value,
                }
            },
        )


def test_sparsity_at_linear_and_cubic():
    assert _sparsity_at(
        1, 2, 0.8, TrainingSparsitySchedule.LINEAR.value
    ) == pytest.approx(0.4)
    assert _sparsity_at(
        1, 2, 0.8, TrainingSparsitySchedule.CUBIC.value
    ) == pytest.approx(0.8 * (0.5**3))
    assert _sparsity_at(
        1, 5, 0.7, TrainingSparsitySchedule.ONE_SHOT.value
    ) == pytest.approx(0.7)


def test_class_weights_inverse_frequency():
    targets = torch.tensor([0, 0, 0, 1])
    weights = _class_weights(targets, 2)
    assert weights[0] < weights[1]


@pytest.mark.skipif(
    importlib.util.find_spec("torchao") is None, reason="torchao is not installed"
)
def test_train_quantize_model_ptq_calls_prepare_and_convert():
    model = nn.Linear(4, 4)
    converted = MagicMock(name="converted")
    exported = MagicMock(name="exported")
    exported.module.return_value = model
    prepared = MagicMock(name="prepared")
    loaders = {
        "train": _linear_loader(),
        "calibrate": _linear_loader(),
    }
    spec = {
        "stage": TrainingStage.QUANTIZE.value,
        "quantize": {"method": TrainingQuantizeMethod.PTQ.value},
    }
    with (
        patch("torch.export.export", return_value=exported),
        patch("src.train_model._x86_quantizer", return_value=object()),
        patch(
            "torchao.quantization.pt2e.quantize_pt2e.prepare_pt2e",
            return_value=prepared,
        ) as prepare,
        patch(
            "torchao.quantization.pt2e.quantize_pt2e.convert_pt2e",
            return_value=converted,
        ) as convert,
        patch("torchao.quantization.pt2e.allow_exported_model_train_eval"),
    ):
        result = train_model(model, loaders, spec)
    prepare.assert_called_once()
    convert.assert_called_once_with(prepared)
    assert result is converted
    assert spec["example_shape"] == [4, 4]
