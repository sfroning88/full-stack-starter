"""
Author: Sean Froning
Created Date: 8.29.2026
Evaluate model performance
"""

import torch.nn as nn
from torch import Tensor, device
from torch.utils.data import DataLoader
from decimal import Decimal
from typing import Callable, List, Optional, Tuple
from fiery_python import (
    STORAGE_OP_VERSION,
    ModelTier,
    ModelRole,
    ModelMetricName,
    TrainingStage,
    TrainingSplit,
    ModelMetric,
    UuidUtils,
)

_SCREENER_MIN_PRECISION = 0.80


def score_model(
    spec: dict,
    model: nn.Module,
    loaders: dict[str, DataLoader],
) -> Tuple[List[ModelMetric], dict]:
    session_id = spec["session_id"]
    if not session_id or not isinstance(session_id, str):
        raise RuntimeError("Missing session_id from spec")
    artifact_id = UuidUtils.deterministic_uuid(session_id)
    stage = spec["stage"]
    tier = spec["tier"]
    role = spec["role"]
    if (
        not stage
        or not tier
        or not role
        or not isinstance(stage, str)
        or not isinstance(tier, str)
        or not isinstance(role, str)
    ):
        raise RuntimeError("Missing (stage, tier, role) from spec")
    match (stage, tier, role):
        case (
            TrainingStage.LORA.value,
            ModelTier.CLOUD.value,
            ModelRole.SCREENER.value,
        ):
            return _score_screener_model(model, loaders, artifact_id, spec)
        case (
            TrainingStage.PRETRAIN.value,
            ModelTier.CLOUD.value,
            ModelRole.TEACHER.value,
        ):
            return _score_teacher_or_student_model(
                model,
                loaders,
                artifact_id,
                spec,
                name=ModelMetricName.MACRO_F1_SCORE,
                score=_macro_f1,
            )
        case (
            TrainingStage.DISTILL.value
            | TrainingStage.PRUNE.value
            | TrainingStage.QUANTIZE.value,
            ModelTier.EDGE.value,
            ModelRole.STUDENT.value,
        ):
            return _score_teacher_or_student_model(
                model,
                loaders,
                artifact_id,
                spec,
                name=ModelMetricName.ACCURACY,
                score=_accuracy,
            )
        case _:
            raise RuntimeError(
                f"Invalid (stage, tier, role) from spec: ({stage}, {tier}, {role})"
            )


def _score_screener_model(
    model: nn.Module,
    loaders: dict[str, DataLoader],
    artifact_id: str,
    spec: dict,
) -> Tuple[List[ModelMetric], dict]:
    device = next(model.parameters()).device
    model.eval()
    validate = loaders.get(TrainingSplit.VALIDATE.value)
    if not validate:
        raise RuntimeError("Missing validate loader")
    val_probs, val_labels = _collect_positive_probs(model, validate, device)
    threshold = _tune_screener_threshold(val_probs, val_labels)
    metrics: List[ModelMetric] = []
    for split in (TrainingSplit.TEST, TrainingSplit.HOLDOUT):
        loader = loaders.get(split.value)
        if not loader:
            continue
        probs, labels = _collect_positive_probs(model, loader, device)
        recall, precision, fpr, abstention_rate = _screener_scores(
            probs, labels, threshold
        )
        if fpr is None:
            raise RuntimeError(
                f"Unmeasured FPR: {split.value} split has no negative labels"
            )
        metrics.extend(
            [
                ModelMetric(
                    name=ModelMetricName.RECALL,
                    split=split,
                    value=Decimal(str(round(recall, 6))),
                    artifact_id=artifact_id,
                ),
                ModelMetric(
                    name=ModelMetricName.PRECISION,
                    split=split,
                    value=Decimal(str(round(precision, 6))),
                    artifact_id=artifact_id,
                ),
                ModelMetric(
                    name=ModelMetricName.FALSE_POSITIVE_RATE,
                    split=split,
                    value=Decimal(str(round(fpr, 6))),
                    artifact_id=artifact_id,
                ),
                ModelMetric(
                    name=ModelMetricName.ABSTENTION_RATE,
                    split=split,
                    value=Decimal(str(round(abstention_rate, 6))),
                    artifact_id=artifact_id,
                ),
            ]
        )
    if not metrics:
        raise RuntimeError("Missing test or holdout loader")
    return metrics, _decision(spec, threshold)


def _score_teacher_or_student_model(
    model: nn.Module,
    loaders: dict[str, DataLoader],
    artifact_id: str,
    spec: dict,
    *,
    name: ModelMetricName,
    score: Callable[[Tensor, Tensor], float],
) -> Tuple[List[ModelMetric], dict]:
    device = _model_device(model)
    model.eval()
    metrics: List[ModelMetric] = []
    for split in (TrainingSplit.TEST, TrainingSplit.HOLDOUT):
        loader = loaders.get(split.value)
        if not loader:
            continue
        preds, labels = _collect_preds(model, loader, device)
        metrics.append(
            ModelMetric(
                name=name,
                split=split,
                value=Decimal(str(round(score(preds, labels), 6))),
                artifact_id=artifact_id,
            )
        )
    if not metrics:
        raise RuntimeError("Missing test or holdout loader")
    return metrics, _decision(spec, 0.0)


def _decision(spec: dict, threshold: float) -> dict:
    transform_hash = spec["shard_prefix"].rstrip("/").rsplit("/", 1)[-1]
    if not transform_hash or not isinstance(transform_hash, str):
        raise RuntimeError("Invalid compiled transform_hash")
    return {
        "threshold": round(threshold, 5),
        "abstention_band": "0.00000",
        "transform_hash": transform_hash,
        "op_version": STORAGE_OP_VERSION,
    }


def _model_device(model: nn.Module) -> device:
    import torch

    try:
        return next(model.parameters()).device
    except StopIteration:
        return torch.device("cpu")


def _collect_preds(
    model: nn.Module,
    loader: DataLoader,
    device: device,
) -> Tuple[Tensor, Tensor]:
    import torch

    preds = []
    labels = []
    with torch.no_grad():
        for features, targets in loader:
            logits = model(features.to(device))
            preds.append(logits.argmax(dim=1).cpu())
            labels.append(targets.cpu())
    if not preds:
        raise RuntimeError("Empty split while scoring")
    return torch.cat(preds), torch.cat(labels)


def _macro_f1(preds: Tensor, labels: Tensor) -> float:
    num_classes = int(max(int(labels.max().item()), int(preds.max().item())) + 1)
    scores = []
    for index in range(num_classes):
        true_positive = int(((preds == index) & (labels == index)).sum().item())
        false_positive = int(((preds == index) & (labels != index)).sum().item())
        false_negative = int(((preds != index) & (labels == index)).sum().item())
        precision = (
            0.0
            if true_positive + false_positive == 0
            else true_positive / (true_positive + false_positive)
        )
        recall = (
            0.0
            if true_positive + false_negative == 0
            else true_positive / (true_positive + false_negative)
        )
        if precision + recall == 0:
            scores.append(0.0)
            continue
        scores.append(2.0 * precision * recall / (precision + recall))
    if not scores:
        raise RuntimeError("Empty split while scoring")
    return sum(scores) / len(scores)


def _accuracy(preds: Tensor, labels: Tensor) -> float:
    if int(labels.numel()) == 0:
        raise RuntimeError("Empty split while scoring")
    return float((preds == labels).sum().item()) / int(labels.numel())


def _collect_positive_probs(
    model: nn.Module,
    loader: DataLoader,
    device: device,
) -> Tuple[Tensor, Tensor]:
    import torch

    probs = []
    labels = []
    with torch.no_grad():
        for images, targets in loader:
            logits = model(images.to(device))
            positive = torch.softmax(logits, dim=1)[:, 1]
            probs.append(positive.cpu())
            labels.append(targets.cpu())
    return torch.cat(probs), torch.cat(labels)


def _screener_scores(
    probs: Tensor, labels: Tensor, threshold: float
) -> Tuple[float, float, Optional[float], float]:
    predicted_positive = probs >= threshold
    num_labels = int(labels.numel())
    if num_labels == 0:
        raise RuntimeError("Empty split while scoring")
    abstention_rate = float((~predicted_positive).sum().item()) / num_labels
    positives = int((labels == 1).sum().item())
    negatives = int((labels == 0).sum().item())
    true_positive = int(((labels == 1) & predicted_positive).sum().item())
    false_positive = int(((labels == 0) & predicted_positive).sum().item())
    predicted_count = int(predicted_positive.sum().item())
    recall = 0.0 if positives == 0 else true_positive / positives
    precision = 0.0 if predicted_count == 0 else true_positive / predicted_count
    fpr = None if negatives == 0 else false_positive / negatives
    return recall, precision, fpr, abstention_rate


def _tune_screener_threshold(probs: Tensor, labels: Tensor) -> float:
    import torch

    candidates = torch.linspace(0.50, 0.95, steps=10)
    feasible: Optional[Tuple[float, float, float]] = None
    fallback = (float("-inf"), float("-inf"), float("inf"), 0.50)
    for threshold in candidates:
        value = float(threshold)
        recall, precision, _fpr, abstention_rate = _screener_scores(
            probs, labels, value
        )
        if precision >= _SCREENER_MIN_PRECISION:
            candidate = (recall, abstention_rate, value)
            if (
                feasible is None
                or candidate[0] > feasible[0]
                or (candidate[0] == feasible[0] and candidate[1] < feasible[1])
            ):
                feasible = candidate
        ranked = (precision, recall, -abstention_rate, value)
        if ranked[:-1] > fallback[:-1]:
            fallback = ranked
    if feasible is not None:
        return feasible[2]
    return fallback[3]
