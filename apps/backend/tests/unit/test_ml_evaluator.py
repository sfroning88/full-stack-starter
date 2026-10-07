"""
Author: Sean Froning
Created Date: 8.26.2026
Unit tests for the model evaluator
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch

from fiery_python import (
    MlflowTrackingServices,
    ModelArtifact,
    ModelMetric,
    ModelMetricName,
    ModelRole,
    ModelTier,
    TrainingPrecision,
    TrainingSplit,
    TrainingStage,
)
from ml.evaluate import _ModelEvaluator, model_evaluator

NOW = datetime.now(tz=timezone.utc)
SCREENER_KEY = (ModelTier.CLOUD, ModelRole.SCREENER)


def _artifact(
    *,
    artifact_id: str = "11111111-1111-1111-1111-111111111111",
    tier: ModelTier = ModelTier.CLOUD,
    role: ModelRole = ModelRole.SCREENER,
    stage: TrainingStage = TrainingStage.LORA,
    precision: TrainingPrecision = TrainingPrecision.FP32,
    param_count: int = 1_000,
    sparsity: Decimal = Decimal("0"),
    session_id: str = "22222222-2222-2222-2222-222222222222",
    mlflow_run_id: str | None = None,
) -> ModelArtifact:
    return ModelArtifact(
        id=artifact_id,
        tier=tier,
        role=role,
        stage=stage,
        precision=precision,
        architecture="cnn",
        param_count=param_count,
        sparsity=sparsity,
        storage_path="models/art.safetensors",
        signature="a" * 64,
        signed_at=NOW,
        promoted=False,
        session_id=session_id,
        mlflow_run_id=mlflow_run_id,
    )


def _metric(
    name: ModelMetricName,
    value: Decimal,
    *,
    artifact_id: str = "11111111-1111-1111-1111-111111111111",
    split: TrainingSplit = TrainingSplit.HOLDOUT,
) -> ModelMetric:
    return ModelMetric(
        name=name,
        split=split,
        value=value,
        artifact_id=artifact_id,
    )


def test_metric_value_prefers_holdout_over_test():
    metrics = [
        _metric(ModelMetricName.RECALL, Decimal("0.10"), split=TrainingSplit.TEST),
        _metric(ModelMetricName.RECALL, Decimal("0.90"), split=TrainingSplit.HOLDOUT),
        _metric(ModelMetricName.RECALL, Decimal("0.50"), split=TrainingSplit.VALIDATE),
    ]

    assert model_evaluator._metric_value(metrics, ModelMetricName.RECALL) == Decimal(
        "0.90"
    )


def test_metric_value_returns_none_when_name_missing():
    metrics = [_metric(ModelMetricName.ACCURACY, Decimal("0.80"))]

    assert model_evaluator._metric_value(metrics, ModelMetricName.RECALL) is None


def _screener_metrics(
    recall: str = "0.80",
    precision: str = "0.80",
    fpr: str = "0.02",
    abstention_rate: str = "0.10",
) -> list[ModelMetric]:
    return [
        _metric(ModelMetricName.RECALL, Decimal(recall)),
        _metric(ModelMetricName.PRECISION, Decimal(precision)),
        _metric(ModelMetricName.FALSE_POSITIVE_RATE, Decimal(fpr)),
        _metric(ModelMetricName.ABSTENTION_RATE, Decimal(abstention_rate)),
    ]


def test_gate_check_promotes_screener_when_slot_empty():
    challenger = _artifact()

    with patch.object(
        _ModelEvaluator, "_fetch_metrics", return_value=_screener_metrics()
    ):
        assert model_evaluator._gate_check(challenger, []) is True


def test_gate_check_rejects_screener_missing_precision():
    challenger = _artifact()
    challenger_metrics = [
        _metric(ModelMetricName.RECALL, Decimal("0.80")),
        _metric(ModelMetricName.FALSE_POSITIVE_RATE, Decimal("0.02")),
    ]

    with patch.object(
        _ModelEvaluator, "_fetch_metrics", return_value=challenger_metrics
    ):
        assert model_evaluator._gate_check(challenger, []) is False


def test_gate_check_rejects_screener_missing_fpr():
    challenger = _artifact()
    challenger_metrics = [
        _metric(ModelMetricName.RECALL, Decimal("0.80")),
        _metric(ModelMetricName.PRECISION, Decimal("0.80")),
        _metric(ModelMetricName.ABSTENTION_RATE, Decimal("0.10")),
    ]

    with patch.object(
        _ModelEvaluator, "_fetch_metrics", return_value=challenger_metrics
    ):
        assert model_evaluator._gate_check(challenger, []) is False


def test_gate_check_rejects_screener_with_high_fpr():
    challenger = _artifact()

    with patch.object(
        _ModelEvaluator,
        "_fetch_metrics",
        return_value=_screener_metrics(fpr="0.10"),
    ):
        assert model_evaluator._gate_check(challenger, []) is False


def test_gate_check_rejects_screener_with_lower_recall():
    challenger = _artifact()
    incumbent_metrics = _screener_metrics(recall="0.80")

    with patch.object(
        _ModelEvaluator,
        "_fetch_metrics",
        return_value=_screener_metrics(recall="0.50"),
    ):
        assert model_evaluator._gate_check(challenger, incumbent_metrics) is False


def test_gate_check_rejects_screener_on_recall_tie():
    challenger = _artifact()
    metrics = _screener_metrics(recall="0.80")

    with patch.object(_ModelEvaluator, "_fetch_metrics", return_value=metrics):
        assert model_evaluator._gate_check(challenger, metrics) is False


def test_gate_check_promotes_screener_when_recall_delta_holds():
    challenger = _artifact()

    with patch.object(
        _ModelEvaluator,
        "_fetch_metrics",
        return_value=_screener_metrics(recall="0.82"),
    ):
        assert (
            model_evaluator._gate_check(challenger, _screener_metrics(recall="0.80"))
            is True
        )


def test_gate_check_promotes_screener_on_min_recall_delta_with_higher_abstention():
    challenger = _artifact()
    incumbent = _screener_metrics(recall="0.80", abstention_rate="0.25")

    with patch.object(
        _ModelEvaluator,
        "_fetch_metrics",
        return_value=_screener_metrics(recall="0.81", abstention_rate="0.20"),
    ):
        assert model_evaluator._gate_check(challenger, incumbent) is True


def test_gate_check_rejects_screener_on_min_recall_delta_without_higher_abstention():
    challenger = _artifact()
    incumbent = _screener_metrics(recall="0.80", abstention_rate="0.10")

    with patch.object(
        _ModelEvaluator,
        "_fetch_metrics",
        return_value=_screener_metrics(recall="0.81", abstention_rate="0.10"),
    ):
        assert model_evaluator._gate_check(challenger, incumbent) is False


def test_gate_check_rejects_teacher_below_min_macro_f1():
    challenger = _artifact(
        artifact_id="33333333-3333-3333-3333-333333333333",
        tier=ModelTier.CLOUD,
        role=ModelRole.TEACHER,
        stage=TrainingStage.PRETRAIN,
    )
    metrics = [_metric(ModelMetricName.MACRO_F1_SCORE, Decimal("0.70"))]

    with patch.object(_ModelEvaluator, "_fetch_metrics", return_value=metrics):
        assert model_evaluator._gate_check(challenger, []) is False


def test_budget_check_passes_cloud_without_upsert():
    challenger = _artifact()

    with patch.object(_ModelEvaluator, "_upsert_budget") as upsert:
        assert model_evaluator._budget_check(challenger, NOW) is True
        upsert.assert_not_called()


def test_budget_check_rejects_oversized_student():
    challenger = _artifact(
        artifact_id="44444444-4444-4444-4444-444444444444",
        tier=ModelTier.EDGE,
        role=ModelRole.STUDENT,
        stage=TrainingStage.QUANTIZE,
        precision=TrainingPrecision.INT8,
        param_count=80_000_000,
        sparsity=Decimal("0"),
    )

    with patch.object(_ModelEvaluator, "_upsert_budget") as upsert:
        assert model_evaluator._budget_check(challenger, NOW) is False
        upsert.assert_called_once()
        budget = upsert.call_args[0][0]
        assert budget.passed is False
        assert budget.artifact_id == challenger.id


def test_budget_check_accepts_sparse_int8_student():
    challenger = _artifact(
        artifact_id="55555555-5555-5555-5555-555555555555",
        tier=ModelTier.EDGE,
        role=ModelRole.STUDENT,
        stage=TrainingStage.QUANTIZE,
        precision=TrainingPrecision.INT8,
        param_count=40_000,
        sparsity=Decimal("0.7"),
    )

    with patch.object(_ModelEvaluator, "_upsert_budget") as upsert:
        assert model_evaluator._budget_check(challenger, NOW) is True
        assert upsert.call_args[0][0].passed is True


def test_run_returns_empty_when_no_challengers():
    with (
        patch.object(_ModelEvaluator, "_fetch_challengers", return_value=[]),
        patch.object(_ModelEvaluator, "_fetch_incumbent", return_value=None),
    ):
        assert model_evaluator.run() == []


def test_run_records_unknown_slot_instead_of_dropping_it():
    challenger = _artifact(tier=ModelTier.EDGE, role=ModelRole.TEACHER)

    with (
        patch.object(_ModelEvaluator, "_fetch_challengers", return_value=[challenger]),
        patch.object(_ModelEvaluator, "_fetch_incumbent", return_value=None),
        patch.object(_ModelEvaluator, "_upsert_artifact") as upsert,
    ):
        results = model_evaluator.run()

    assert len(results) == 1
    assert results[0].promoted is False
    assert results[0].denied_reason == "Challenger not in model registry slots"
    upsert.assert_not_called()


def test_run_promotes_winning_screener_aliases_mlflow_version_for_run():
    challenger = _artifact(mlflow_run_id="run-challenger")
    incumbent = _artifact(
        artifact_id="66666666-6666-6666-6666-666666666666",
        session_id="77777777-7777-7777-7777-777777777777",
    )
    incumbent.promoted = True
    challenger_metrics = _screener_metrics(recall="0.90")
    incumbent_metrics = _screener_metrics(recall="0.70")

    def fake_incumbent(key):
        if key == SCREENER_KEY:
            return incumbent
        return None

    def fake_metrics(artifact_id, limit=10):
        if artifact_id == incumbent.id:
            return incumbent_metrics
        return challenger_metrics

    with (
        patch.object(_ModelEvaluator, "_fetch_challengers", return_value=[challenger]),
        patch.object(_ModelEvaluator, "_fetch_incumbent", side_effect=fake_incumbent),
        patch.object(_ModelEvaluator, "_fetch_metrics", side_effect=fake_metrics),
        patch.object(_ModelEvaluator, "_upsert_artifact") as upsert_artifact,
        patch.object(_ModelEvaluator, "_upsert_budget") as upsert_budget,
        patch.object(
            MlflowTrackingServices,
            "registered_version_for_run",
            return_value="4",
        ) as resolve_version,
        patch.object(
            MlflowTrackingServices,
            "alias_production",
        ) as alias_production,
    ):
        results = model_evaluator.run()

    assert len(results) == 1
    assert results[0].promoted is True
    resolve_version.assert_called_once_with("Fiery-Screener", "run-challenger")
    alias_production.assert_called_once_with("Fiery-Screener", version="4")
    upsert_artifact.assert_called_once()
    upsert_budget.assert_not_called()


def test_run_promotes_winning_screener_skips_mlflow_when_run_id_missing():
    challenger = _artifact()
    incumbent = _artifact(
        artifact_id="66666666-6666-6666-6666-666666666666",
        session_id="77777777-7777-7777-7777-777777777777",
    )
    incumbent.promoted = True
    challenger_metrics = _screener_metrics(recall="0.90")
    incumbent_metrics = _screener_metrics(recall="0.70")

    def fake_incumbent(key):
        if key == SCREENER_KEY:
            return incumbent
        return None

    def fake_metrics(artifact_id, limit=10):
        if artifact_id == incumbent.id:
            return incumbent_metrics
        return challenger_metrics

    with (
        patch.object(_ModelEvaluator, "_fetch_challengers", return_value=[challenger]),
        patch.object(_ModelEvaluator, "_fetch_incumbent", side_effect=fake_incumbent),
        patch.object(_ModelEvaluator, "_fetch_metrics", side_effect=fake_metrics),
        patch.object(_ModelEvaluator, "_upsert_artifact") as upsert_artifact,
        patch.object(_ModelEvaluator, "_upsert_budget") as upsert_budget,
        patch.object(
            MlflowTrackingServices,
            "registered_version_for_run",
        ) as resolve_version,
        patch.object(
            MlflowTrackingServices,
            "alias_production",
        ) as alias_production,
    ):
        results = model_evaluator.run()

    assert len(results) == 1
    assert results[0].promoted is True
    assert results[0].ready is False
    assert results[0].denied_reason is None
    upsert_artifact.assert_called_once()
    promoted = upsert_artifact.call_args[0][0]
    assert promoted.id == challenger.id
    assert promoted.promoted is True
    assert incumbent.promoted is True
    upsert_budget.assert_not_called()
    resolve_version.assert_not_called()
    alias_production.assert_not_called()


def test_run_can_promote_multiple_challengers_without_demoting_incumbent():
    first = _artifact()
    second = _artifact(
        artifact_id="99999999-9999-9999-9999-999999999999",
        session_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    )
    incumbent = _artifact(
        artifact_id="66666666-6666-6666-6666-666666666666",
        session_id="77777777-7777-7777-7777-777777777777",
    )
    incumbent.promoted = True
    winning = _screener_metrics(recall="0.90")
    incumbent_metrics = _screener_metrics(recall="0.70")

    def fake_incumbent(key):
        if key == SCREENER_KEY:
            return incumbent
        return None

    def fake_metrics(artifact_id, limit=10):
        if artifact_id == incumbent.id:
            return incumbent_metrics
        return winning

    with (
        patch.object(
            _ModelEvaluator, "_fetch_challengers", return_value=[first, second]
        ),
        patch.object(_ModelEvaluator, "_fetch_incumbent", side_effect=fake_incumbent),
        patch.object(_ModelEvaluator, "_fetch_metrics", side_effect=fake_metrics),
        patch.object(_ModelEvaluator, "_upsert_artifact") as upsert_artifact,
        patch.object(_ModelEvaluator, "_upsert_budget"),
    ):
        results = model_evaluator.run()

    assert [row.promoted for row in results] == [True, True]
    assert upsert_artifact.call_count == 2
    upserted_ids = [call[0][0].id for call in upsert_artifact.call_args_list]
    assert upserted_ids == [first.id, second.id]
    assert all(call[0][0].promoted is True for call in upsert_artifact.call_args_list)
    assert incumbent.promoted is True


def test_run_denies_student_that_fails_budget_after_winning_gate():
    challenger = _artifact(
        artifact_id="88888888-8888-8888-8888-888888888888",
        tier=ModelTier.EDGE,
        role=ModelRole.STUDENT,
        stage=TrainingStage.QUANTIZE,
        precision=TrainingPrecision.INT8,
        param_count=80_000_000,
    )

    with (
        patch.object(_ModelEvaluator, "_fetch_challengers", return_value=[challenger]),
        patch.object(_ModelEvaluator, "_fetch_incumbent", return_value=None),
        patch.object(
            _ModelEvaluator,
            "_fetch_metrics",
            return_value=[_metric(ModelMetricName.ACCURACY, Decimal("0.95"))],
        ),
        patch.object(_ModelEvaluator, "_upsert_artifact") as upsert_artifact,
        patch.object(_ModelEvaluator, "_upsert_budget") as upsert_budget,
    ):
        results = model_evaluator.run()

    assert results[0].promoted is False
    assert results[0].denied_reason == "Failed to pass edge device budget"
    upsert_artifact.assert_not_called()
    upsert_budget.assert_called_once()
