"""
Author: Sean Froning
Created Date: 8.29.2026
Unit tests for trainer scoring
"""

from decimal import Decimal
from unittest.mock import patch

import pytest
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
from fiery_python import (
    STORAGE_OP_VERSION,
    ModelMetricName,
    ModelRole,
    ModelTier,
    TrainingStage,
    TrainingSplit,
    UuidUtils,
)
from src.score_model import (
    _accuracy,
    _macro_f1,
    _screener_scores,
    _tune_screener_threshold,
    score_model,
)


class _ConstLogits(nn.Module):
    def __init__(self, positive_logit: float) -> None:
        super().__init__()
        self.bias = nn.Parameter(torch.zeros(1))
        self.positive_logit = positive_logit

    def forward(self, images: torch.Tensor) -> torch.Tensor:
        batch = images.shape[0]
        logits = torch.zeros(batch, 2)
        logits[:, 1] = self.positive_logit
        return logits + self.bias


def _loader(labels: list[int]) -> DataLoader:
    images = torch.zeros(len(labels), 3, 8, 8)
    targets = torch.tensor(labels, dtype=torch.long)
    return DataLoader(TensorDataset(images, targets), batch_size=len(labels))


def _score_spec(**overrides) -> dict:
    data = {
        "session_id": "sess-1",
        "stage": TrainingStage.LORA.value,
        "tier": ModelTier.CLOUD.value,
        "role": ModelRole.SCREENER.value,
        "shard_prefix": "contract-1/" + ("a" * 64) + "/",
    }
    data.update(overrides)
    return data


def test_score_model_raises_when_session_missing():
    with pytest.raises(RuntimeError, match="Missing session_id from spec"):
        score_model({"session_id": None}, _ConstLogits(10.0), {})


def test_score_model_raises_when_slot_invalid():
    with pytest.raises(RuntimeError, match="Invalid \\(stage, tier, role\\)"):
        score_model(
            _score_spec(role=ModelRole.TEACHER.value),
            _ConstLogits(10.0),
            {},
        )


def test_score_model_dispatches_teacher():
    expected = ([object()], {"op_version": 1})
    with patch(
        "src.score_model._score_teacher_or_student_model", return_value=expected
    ) as score:
        result = score_model(
            _score_spec(
                stage=TrainingStage.PRETRAIN.value,
                role=ModelRole.TEACHER.value,
            ),
            _ConstLogits(1.0),
            {},
        )
    assert result is expected
    score.assert_called_once()
    assert score.call_args.kwargs["name"] is ModelMetricName.MACRO_F1_SCORE
    assert score.call_args.kwargs["score"] is _macro_f1


def test_score_model_dispatches_student():
    expected = ([object()], {"op_version": 1})
    with patch(
        "src.score_model._score_teacher_or_student_model", return_value=expected
    ) as score:
        result = score_model(
            _score_spec(
                stage=TrainingStage.DISTILL.value,
                tier=ModelTier.EDGE.value,
                role=ModelRole.STUDENT.value,
            ),
            _ConstLogits(1.0),
            {},
        )
    assert result is expected
    score.assert_called_once()
    assert score.call_args.kwargs["name"] is ModelMetricName.ACCURACY
    assert score.call_args.kwargs["score"] is _accuracy


def test_screener_scores_counts_abstain_as_miss():
    probs = torch.tensor([0.9, 0.1, 0.8])
    labels = torch.tensor([1, 1, 0])
    recall, precision, fpr, abstention = _screener_scores(probs, labels, 0.5)
    assert recall == pytest.approx(0.5)
    assert precision == pytest.approx(0.5)
    assert fpr == pytest.approx(1.0)
    assert abstention == pytest.approx(1 / 3)


def test_screener_scores_zero_recall_without_positives():
    probs = torch.tensor([0.2, 0.1])
    labels = torch.tensor([0, 0])
    recall, precision, fpr, abstention = _screener_scores(probs, labels, 0.5)
    assert recall == 0.0
    assert precision == 0.0
    assert fpr == pytest.approx(0.0)
    assert abstention == pytest.approx(1.0)


def test_screener_scores_omits_fpr_without_negatives():
    probs = torch.tensor([0.9, 0.8])
    labels = torch.tensor([1, 1])
    recall, precision, fpr, abstention = _screener_scores(probs, labels, 0.5)
    assert recall == pytest.approx(1.0)
    assert precision == pytest.approx(1.0)
    assert fpr is None
    assert abstention == pytest.approx(0.0)


def test_screener_scores_rejects_empty_split():
    with pytest.raises(RuntimeError, match="Empty split while scoring"):
        _screener_scores(torch.tensor([]), torch.tensor([]), 0.5)


def test_tune_screener_threshold_keeps_lowest_when_precision_already_holds():
    probs = torch.tensor([0.9, 0.9, 0.2])
    labels = torch.tensor([1, 1, 0])
    threshold = _tune_screener_threshold(probs, labels)
    recall, _precision, _fpr, _abstention = _screener_scores(probs, labels, threshold)
    assert recall == pytest.approx(1.0)
    assert threshold == pytest.approx(0.50)


def test_tune_screener_threshold_raises_until_precision_floor():
    probs = torch.tensor([0.91, 0.91, 0.62])
    labels = torch.tensor([1, 1, 0])
    threshold = _tune_screener_threshold(probs, labels)
    assert threshold > 0.62
    recall, _precision, _fpr, _abstention = _screener_scores(probs, labels, threshold)
    assert recall == pytest.approx(1.0)


def test_score_model_emits_recall_and_abstention_for_test_and_holdout():
    loaders = {
        TrainingSplit.VALIDATE.value: _loader([1, 0]),
        TrainingSplit.TEST.value: _loader([1, 1, 0]),
        TrainingSplit.HOLDOUT.value: _loader([1, 0]),
    }
    metrics, decision = score_model(_score_spec(), _ConstLogits(10.0), loaders)
    artifact_id = UuidUtils.deterministic_uuid("sess-1")
    names = {(metric.name, metric.split) for metric in metrics}
    assert names == {
        (ModelMetricName.RECALL, TrainingSplit.TEST),
        (ModelMetricName.PRECISION, TrainingSplit.TEST),
        (ModelMetricName.FALSE_POSITIVE_RATE, TrainingSplit.TEST),
        (ModelMetricName.ABSTENTION_RATE, TrainingSplit.TEST),
        (ModelMetricName.RECALL, TrainingSplit.HOLDOUT),
        (ModelMetricName.PRECISION, TrainingSplit.HOLDOUT),
        (ModelMetricName.FALSE_POSITIVE_RATE, TrainingSplit.HOLDOUT),
        (ModelMetricName.ABSTENTION_RATE, TrainingSplit.HOLDOUT),
    }
    assert all(metric.artifact_id == artifact_id for metric in metrics)
    assert all(isinstance(metric.value, Decimal) for metric in metrics)
    assert decision["transform_hash"] == "a" * 64
    assert decision["op_version"] == STORAGE_OP_VERSION
    assert decision["abstention_band"] == "0.00000"


def test_score_model_requires_validate_loader():
    with pytest.raises(RuntimeError, match="Missing validate loader"):
        score_model(
            _score_spec(),
            _ConstLogits(10.0),
            {TrainingSplit.TEST.value: _loader([1])},
        )


def test_score_model_requires_test_or_holdout():
    with pytest.raises(RuntimeError, match="Missing test or holdout loader"):
        score_model(
            _score_spec(),
            _ConstLogits(10.0),
            {TrainingSplit.VALIDATE.value: _loader([1, 0])},
        )


def test_score_model_raises_when_scored_split_has_no_negatives():
    loaders = {
        TrainingSplit.VALIDATE.value: _loader([1, 0]),
        TrainingSplit.TEST.value: _loader([1, 1]),
    }
    with pytest.raises(RuntimeError, match="Unmeasured FPR"):
        score_model(_score_spec(), _ConstLogits(10.0), loaders)


def test_score_model_dispatches_screener():
    expected = ([object()], {"op_version": 1})
    with patch("src.score_model._score_screener_model", return_value=expected) as score:
        result = score_model(_score_spec(), _ConstLogits(1.0), {})
    assert result is expected
    score.assert_called_once()
    assert score.call_args[0][2] == UuidUtils.deterministic_uuid("sess-1")


def test_macro_f1_is_one_when_perfect():
    preds = torch.tensor([0, 1, 2, 3])
    labels = torch.tensor([0, 1, 2, 3])
    assert _macro_f1(preds, labels) == pytest.approx(1.0)


def test_accuracy_is_half_when_half_correct():
    preds = torch.tensor([0, 1, 2, 3])
    labels = torch.tensor([0, 1, 0, 0])
    assert _accuracy(preds, labels) == pytest.approx(0.5)


def test_score_teacher_emits_macro_f1():
    class _FourWay(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.bias = nn.Parameter(torch.zeros(1))

        def forward(self, features: torch.Tensor) -> torch.Tensor:
            batch = features.shape[0]
            logits = torch.zeros(batch, 4)
            logits[:, 0] = 10.0
            return logits + self.bias

    loaders = {
        TrainingSplit.TEST.value: _loader([0, 0]),
        TrainingSplit.HOLDOUT.value: _loader([0, 1]),
    }
    metrics, decision = score_model(
        _score_spec(
            stage=TrainingStage.PRETRAIN.value,
            role=ModelRole.TEACHER.value,
        ),
        _FourWay(),
        loaders,
    )
    names = {(metric.name, metric.split) for metric in metrics}
    assert names == {
        (ModelMetricName.MACRO_F1_SCORE, TrainingSplit.TEST),
        (ModelMetricName.MACRO_F1_SCORE, TrainingSplit.HOLDOUT),
    }
    assert decision["threshold"] == 0.0
    assert decision["op_version"] == STORAGE_OP_VERSION


def test_score_student_emits_accuracy():
    class _FourWay(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.bias = nn.Parameter(torch.zeros(1))

        def forward(self, features: torch.Tensor) -> torch.Tensor:
            batch = features.shape[0]
            logits = torch.zeros(batch, 4)
            logits[torch.arange(batch), torch.arange(batch) % 4] = 10.0
            return logits + self.bias

    loaders = {TrainingSplit.TEST.value: _loader([0, 1, 2, 3])}
    metrics, _decision = score_model(
        _score_spec(
            stage=TrainingStage.PRUNE.value,
            tier=ModelTier.EDGE.value,
            role=ModelRole.STUDENT.value,
        ),
        _FourWay(),
        loaders,
    )
    assert len(metrics) == 1
    assert metrics[0].name is ModelMetricName.ACCURACY
    assert metrics[0].value == Decimal("1.000000")
