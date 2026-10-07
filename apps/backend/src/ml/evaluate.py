"""
Author: Sean Froning
Created Date: 8.26.2026
Operations pertaining to ML promotion
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple
from fiery_python import db_pool, logging
from fiery_python import (
    PoolFetch,
    MLFLOW_REGISTERED_MODELS,
    MODEL_REGISTRY_SLOTS,
    MODEL_DB_FETCH_SIZE,
    ModelTier,
    ModelRole,
    ModelMetricName,
    TrainingSplit,
    TrainingPrecision,
    ModelArtifact,
    ModelMetric,
    ModelBudget,
    MlflowTrackingServices,
)
from .models import EvaluatedModel
from .queries.select_challenger_artifacts import QUERY as SELECT_CHALLENGER_ARTIFACTS
from .queries.select_incumbent_artifact import QUERY as SELECT_INCUMBENT_ARTIFACT
from .queries.select_model_metrics import QUERY as SELECT_METRICS
from .queries.upsert_model_artifact import QUERY as UPSERT_ARTIFACT
from .queries.upsert_model_budget import QUERY as UPSERT_BUDGET

logger = logging.get_logger(__name__)

_BYTES_PER_PARAM = {
    TrainingPrecision.FP32: 4,
    TrainingPrecision.FP16: 2,
    TrainingPrecision.INT8: 1,
}
_EDGE_FLASH_BUDGET_KB = Decimal("256")
_EDGE_PEAK_RAM_BUDGET_KB = Decimal("256")
_EDGE_MACS_BUDGET = 50_000_000
_SCREENER_MIN_RECALL = Decimal("0.70")
_SCREENER_MIN_PRECISION = Decimal("0.80")
_SCREENER_MAX_FPR = Decimal("0.05")
_SCREENER_MIN_RECALL_DELTA = Decimal("0.01")
_TEACHER_MIN_MACRO_F1_SCORE = Decimal("0.75")
_TEACHER_MIN_MACRO_F1_SCORE_DELTA = Decimal("0.02")
_STUDENT_MIN_ACCURACY = Decimal("0.80")
_STUDENT_MIN_ACCURACY_DELTA = Decimal("0.02")


class _ModelEvaluator:
    """Evaluate challenger artifacts against incumbents"""

    @classmethod
    def run(cls) -> List[EvaluatedModel]:
        """Evaluate unpromoted challengers and persist any promotions"""
        evaluated_models: List[EvaluatedModel] = []
        challengers = cls._fetch_challengers(MODEL_DB_FETCH_SIZE)
        incumbents = {key: cls._fetch_incumbent(key) for key in MODEL_REGISTRY_SLOTS}
        incumbent_metrics = {
            incumbent.id: cls._fetch_metrics(incumbent.id)
            for key, incumbent in incumbents.items()
            if incumbents[key] and incumbent and incumbent.id
        }
        evaluated_at = datetime.now(timezone.utc)
        for challenger in challengers:
            challenger.id = challenger.id or challenger.deterministic_id()
            if not challenger.id:
                continue
            promoted = False
            promoted_at = None
            denied_reason = None
            try:
                key = (challenger.tier, challenger.role)
                if key not in MODEL_REGISTRY_SLOTS:
                    denied_reason = "Challenger not in model registry slots"
                else:
                    incumbent = incumbents.get(key)
                    metrics_to_beat: List[ModelMetric] = []
                    if incumbent and incumbent.id:
                        metrics_to_beat = incumbent_metrics.get(incumbent.id) or []
                    if cls._gate_check(challenger, metrics_to_beat):
                        if cls._budget_check(challenger, evaluated_at):
                            promoted = True
                            promoted_at = evaluated_at
                            challenger.promoted = True
                            challenger.promoted_at = evaluated_at
                            cls._upsert_artifact(challenger)
                            try:
                                name = MLFLOW_REGISTERED_MODELS[
                                    (challenger.tier, challenger.role)
                                ]
                                run_id = challenger.mlflow_run_id
                                if not run_id:
                                    logger.warning(
                                        "mlflow_alias_skipped",
                                        artifact_id=challenger.id,
                                        reason="missing_mlflow_run_id",
                                    )
                                else:
                                    version = MlflowTrackingServices.registered_version_for_run(
                                        name, run_id
                                    )
                                    MlflowTrackingServices.alias_production(
                                        name, version=version
                                    )
                            except Exception as err:
                                logger.warning("mlflow_alias_failed", error=str(err))
                        else:
                            denied_reason = "Failed to pass edge device budget"
                    else:
                        denied_reason = "Failed to beat incumbent model"
            except Exception as err:
                logger.warning(
                    "model_evaluator_failed",
                    artifact_id=challenger.id,
                    error=str(err),
                )
                promoted = False
                promoted_at = None
                denied_reason = str(err)
            evaluated_models.append(
                EvaluatedModel(
                    artifact_id=challenger.id,
                    tier=challenger.tier,
                    role=challenger.role,
                    evaluated_at=evaluated_at,
                    promoted=promoted,
                    promoted_at=promoted_at,
                    denied_reason=denied_reason,
                    ready=False,
                )
            )
        return evaluated_models

    @classmethod
    def _gate_check(
        cls,
        challenger: ModelArtifact,
        metrics_to_beat: List[ModelMetric],
    ) -> bool:
        key = (challenger.tier, challenger.role)
        if not challenger.id:
            return False
        challenger_metrics = cls._fetch_metrics(challenger.id)
        if not challenger_metrics:
            return False
        match key:
            case (ModelTier.CLOUD, ModelRole.SCREENER):
                return cls._screener_gate(challenger_metrics, metrics_to_beat)
            case (ModelTier.CLOUD, ModelRole.TEACHER):
                return cls._teacher_gate(challenger_metrics, metrics_to_beat)
            case (ModelTier.EDGE, ModelRole.STUDENT):
                return cls._student_gate(challenger_metrics, metrics_to_beat)
            case _:
                return False

    @classmethod
    def _screener_gate(
        cls,
        challenger_metrics: List[ModelMetric],
        metrics_to_beat: List[ModelMetric],
    ) -> bool:
        recall = cls._metric_value(challenger_metrics, ModelMetricName.RECALL)
        precision = cls._metric_value(challenger_metrics, ModelMetricName.PRECISION)
        fpr = cls._metric_value(challenger_metrics, ModelMetricName.FALSE_POSITIVE_RATE)
        abstention_rate = cls._metric_value(
            challenger_metrics, ModelMetricName.ABSTENTION_RATE
        )
        if (
            recall is None
            or precision is None
            or fpr is None
            or abstention_rate is None
        ):
            return False
        if (
            recall < _SCREENER_MIN_RECALL
            or precision < _SCREENER_MIN_PRECISION
            or fpr > _SCREENER_MAX_FPR
        ):
            return False
        incumbent_recall = cls._metric_value(metrics_to_beat, ModelMetricName.RECALL)
        if incumbent_recall is None:
            return True
        incumbent_abstention_rate = cls._metric_value(
            metrics_to_beat, ModelMetricName.ABSTENTION_RATE
        )
        recall_delta = recall - incumbent_recall
        if recall_delta == _SCREENER_MIN_RECALL_DELTA:
            if not incumbent_abstention_rate:
                return True
            return abstention_rate < incumbent_abstention_rate
        return recall_delta >= _SCREENER_MIN_RECALL_DELTA

    @classmethod
    def _teacher_gate(
        cls,
        challenger_metrics: List[ModelMetric],
        metrics_to_beat: List[ModelMetric],
    ) -> bool:
        macro_f1_score = cls._metric_value(
            challenger_metrics, ModelMetricName.MACRO_F1_SCORE
        )
        if macro_f1_score is None:
            return False
        if macro_f1_score < _TEACHER_MIN_MACRO_F1_SCORE:
            return False
        incumbent_macro_f1_score = cls._metric_value(
            metrics_to_beat, ModelMetricName.MACRO_F1_SCORE
        )
        if incumbent_macro_f1_score is None:
            return True
        return (
            macro_f1_score - incumbent_macro_f1_score
            >= _TEACHER_MIN_MACRO_F1_SCORE_DELTA
        )

    @classmethod
    def _student_gate(
        cls,
        challenger_metrics: List[ModelMetric],
        metrics_to_beat: List[ModelMetric],
    ) -> bool:
        accuracy = cls._metric_value(challenger_metrics, ModelMetricName.ACCURACY)
        if accuracy is None:
            return False
        if accuracy < _STUDENT_MIN_ACCURACY:
            return False
        incumbent_accuracy = cls._metric_value(
            metrics_to_beat, ModelMetricName.ACCURACY
        )
        if incumbent_accuracy is None:
            return True
        return accuracy - incumbent_accuracy >= _STUDENT_MIN_ACCURACY_DELTA

    @staticmethod
    def _metric_value(
        metrics: List[ModelMetric],
        name: ModelMetricName,
    ) -> Optional[Decimal]:
        preferred = (
            TrainingSplit.HOLDOUT,
            TrainingSplit.TEST,
            TrainingSplit.VALIDATE,
        )
        by_split = {
            metric.split: metric.value for metric in metrics if metric.name is name
        }
        for split in preferred:
            if split in by_split:
                return by_split[split]
        return None

    @classmethod
    def _budget_check(cls, challenger: ModelArtifact, checked_at: datetime) -> bool:
        if (challenger.tier, challenger.role) != (ModelTier.EDGE, ModelRole.STUDENT):
            return True
        if not challenger.id:
            return False
        bytes_per = _BYTES_PER_PARAM.get(challenger.precision, 4)
        kept_sparsity = Decimal("1") - Decimal(str(challenger.sparsity or 0))
        param_count = Decimal(challenger.param_count or 0)
        flash_kb = param_count * Decimal(bytes_per) * kept_sparsity / Decimal("1024")
        peak_ram_kb = flash_kb
        macs = int(param_count * kept_sparsity)
        passed = (
            flash_kb <= _EDGE_FLASH_BUDGET_KB
            and peak_ram_kb <= _EDGE_PEAK_RAM_BUDGET_KB
            and macs <= _EDGE_MACS_BUDGET
        )
        budget = ModelBudget(
            flash_kb=flash_kb,
            flash_budget_kb=_EDGE_FLASH_BUDGET_KB,
            peak_ram_kb=peak_ram_kb,
            peak_ram_budget_kb=_EDGE_PEAK_RAM_BUDGET_KB,
            macs=macs,
            macs_budget=_EDGE_MACS_BUDGET,
            passed=passed,
            checked_at=checked_at,
            artifact_id=challenger.id,
        )
        cls._upsert_budget(budget)
        return passed

    @staticmethod
    def _fetch_challengers(limit: int = MODEL_DB_FETCH_SIZE) -> List[ModelArtifact]:
        rows = db_pool.run(
            SELECT_CHALLENGER_ARTIFACTS,
            (limit,),
            fetch=PoolFetch.ALL,
            error_event="fetch_model_artifacts_failed",
        )
        if not rows:
            logger.warning("fetch_model_artifacts_empty")
            return []
        artifacts: List[ModelArtifact] = []
        for row in rows:
            artifacts.append(
                ModelArtifact(
                    id=row.get("id"),
                    tier=row.get("tier"),
                    role=row.get("role"),
                    stage=row.get("stage"),
                    precision=row.get("precision"),
                    architecture=row.get("architecture"),
                    param_count=row.get("param_count"),
                    sparsity=row.get("sparsity"),
                    storage_path=row.get("storage_path"),
                    signature=row.get("signature"),
                    signed_at=row.get("signed_at"),
                    promoted=row.get("promoted"),
                    promoted_at=row.get("promoted_at"),
                    mlflow_run_id=row.get("mlflow_run_id"),
                    hf_repo_id=row.get("hf_repo_id"),
                    hf_revision=row.get("hf_revision"),
                    session_id=row.get("session_id"),
                    parent_id=row.get("parent_id"),
                )
            )
        return artifacts

    @staticmethod
    def _fetch_incumbent(key: Tuple[ModelTier, ModelRole]) -> Optional[ModelArtifact]:
        tier, role = key
        row = db_pool.run(
            SELECT_INCUMBENT_ARTIFACT,
            (tier, role),
            fetch=PoolFetch.ONE,
            error_event="fetch_model_artifact_failed",
        )
        if not row:
            logger.warning("fetch_model_artifact_empty", tier=tier, role=role)
            return None
        return ModelArtifact(
            id=row.get("id"),
            tier=tier,
            role=role,
            stage=row.get("stage"),
            precision=row.get("precision"),
            architecture=row.get("architecture"),
            param_count=row.get("param_count"),
            sparsity=row.get("sparsity"),
            storage_path=row.get("storage_path"),
            signature=row.get("signature"),
            signed_at=row.get("signed_at"),
            promoted=row.get("promoted"),
            promoted_at=row.get("promoted_at"),
            mlflow_run_id=row.get("mlflow_run_id"),
            hf_repo_id=row.get("hf_repo_id"),
            hf_revision=row.get("hf_revision"),
            session_id=row.get("session_id"),
            parent_id=row.get("parent_id"),
        )

    @staticmethod
    def _fetch_metrics(artifact_id: str) -> List[ModelMetric]:
        rows = db_pool.run(
            SELECT_METRICS,
            (artifact_id,),
            fetch=PoolFetch.ALL,
            error_event="fetch_model_metrics_failed",
        )
        if not rows:
            logger.warning("fetch_model_metrics_empty")
            return []
        metrics: List[ModelMetric] = []
        for row in rows:
            metrics.append(
                ModelMetric(
                    name=row.get("name"),
                    split=row.get("split"),
                    value=row.get("value"),
                    artifact_id=artifact_id,
                )
            )
        return metrics

    @staticmethod
    def _upsert_artifact(artifact: ModelArtifact) -> None:
        db_pool.run(
            UPSERT_ARTIFACT,
            artifact.prepare_for_storage(include_id=True),
        )

    @staticmethod
    def _upsert_budget(budget: ModelBudget) -> None:
        db_pool.run(
            UPSERT_BUDGET,
            budget.prepare_for_storage(include_id=True),
        )


model_evaluator = _ModelEvaluator()
