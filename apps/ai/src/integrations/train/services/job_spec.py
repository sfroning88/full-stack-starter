"""
Author: Sean Froning
Created Date: 8.28.2026
Processing functions for Train jobs
"""

from typing import Any, Dict, Optional, assert_never
from fiery_python import config, error
from fiery_python import (
    DatasetVersion,
    ModelTier,
    ModelRole,
    ModelArtifact,
    TrainingStage,
    TrainingPrecision,
    TrainingTargetModules,
    TrainingHyperparameterPretrain,
    TrainingHyperparameterLora,
    TrainingHyperparameterDistill,
    TrainingHyperparameterPrune,
    TrainingHyperparameterQuantize,
    TrainingSession,
    TrainingHyperparameter,
)
from .persist_service import TrainPersistService

_VIT_BASE_MODEL_ID = "timm/vit_small_patch16_224.augreg_in21k_ft_in1k"
_VIT_REVISION = "7e2c55630205e1266030f18370f4c6ed1a514b52"


class TrainJobSpec:
    """Build training job Modal kwargs for GPU training"""

    @staticmethod
    def build_job_spec(
        session: TrainingSession,
        version: DatasetVersion,
        hyperparameter: TrainingHyperparameter,
        nonce: str,
        parent_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        ai_api_url = config.get_required("ai_api_url")
        if not ai_api_url or not isinstance(ai_api_url, str):
            raise error("AI_API_URL not configured")
        pretrain, screener, distill, prune, quantize = hyperparameter
        lora = None
        modules = None
        if screener:
            lora, modules = screener
        parent = None
        if parent_id:
            parent = TrainPersistService.select_artifact(parent_id)
        spec = {
            "session_id": session.id,
            "contract_id": session.contract_id,
            "version_id": session.version_id,
            "signal": session.signal.value,
            "stage": session.stage.value,
            "samples": session.samples,
            "seed": session.seed,
            "git_sha": session.git_sha,
            "shard_prefix": f"{version.contract_id}/{version.transform_hash}/",
            "manifest_path": version.manifest_path,
            "callback_url": f"{ai_api_url.rstrip('/')}/api/callback/train",
            "precision": TrainingPrecision.FP32.value,
            "nonce": nonce,
        }
        match session.stage:
            case TrainingStage.PRETRAIN:
                if not pretrain:
                    return None
                return spec | TrainJobSpec.build_pretrain_job_spec(pretrain)
            case TrainingStage.LORA:
                if not lora or not modules:
                    return None
                return spec | TrainJobSpec.build_lora_job_spec(modules, lora)
            case TrainingStage.DISTILL:
                if not distill or not parent:
                    return None
                return spec | TrainJobSpec.build_distill_job_spec(distill, parent)
            case TrainingStage.PRUNE:
                if not prune or not parent:
                    return None
                return spec | TrainJobSpec.build_prune_job_spec(prune, parent)
            case TrainingStage.QUANTIZE:
                if not quantize or not parent:
                    return None
                return spec | TrainJobSpec.build_quantize_job_spec(quantize, parent)
            case _:
                assert_never(session.stage)

    @staticmethod
    def build_pretrain_job_spec(
        pretrain: TrainingHyperparameterPretrain,
    ) -> Dict[str, Any]:
        return {
            "pretrain": {
                "id": pretrain.id,
                "epochs": pretrain.epochs,
                "batch_size": pretrain.batch_size,
                "learning_rate": pretrain.learning_rate,
                "optimizer": pretrain.optimizer.value,
                "weight_decay": str(pretrain.weight_decay),
                "lr_schedule": pretrain.lr_schedule.value,
                "seed": pretrain.seed,
            },
            "tier": ModelTier.CLOUD.value,
            "role": ModelRole.TEACHER.value,
        }

    @staticmethod
    def build_lora_job_spec(
        modules: TrainingTargetModules, lora: TrainingHyperparameterLora
    ) -> Dict[str, Any]:
        return {
            "lora": {
                "id": lora.id,
                "rank": lora.rank,
                "alpha": lora.alpha,
                "dropout": lora.dropout,
                "epochs": lora.epochs,
                "learning_rate": lora.learning_rate,
                "target_modules": {
                    "query": modules.query,
                    "key": modules.key,
                    "value": modules.value,
                    "output": modules.output,
                },
            },
            "base_model_id": _VIT_BASE_MODEL_ID,
            "revision": _VIT_REVISION,
            "tier": ModelTier.CLOUD.value,
            "role": ModelRole.SCREENER.value,
        }

    @staticmethod
    def build_distill_job_spec(
        distill: TrainingHyperparameterDistill,
        parent: ModelArtifact,
    ) -> Dict[str, Any]:
        return {
            "distill": {
                "id": distill.id,
                "temperature": distill.temperature,
                "alpha": str(distill.alpha),
                "epochs": distill.epochs,
                "batch_size": distill.batch_size,
                "learning_rate": distill.learning_rate,
                "student_architecture": distill.student_architecture,
            },
            "tier": ModelTier.EDGE.value,
            "role": ModelRole.STUDENT.value,
        } | TrainJobSpec._parent_fields(parent)

    @staticmethod
    def build_prune_job_spec(
        prune: TrainingHyperparameterPrune,
        parent: ModelArtifact,
    ) -> Dict[str, Any]:
        return {
            "prune": {
                "id": prune.id,
                "target_sparsity": str(prune.target_sparsity),
                "iterations": prune.iterations,
                "sparsity_schedule": prune.sparsity_schedule.value,
                "finetune_epochs_per_iter": prune.finetune_epochs_per_iter,
                "pruning_criterion": prune.pruning_criterion.value,
            },
            "tier": ModelTier.EDGE.value,
            "role": ModelRole.STUDENT.value,
        } | TrainJobSpec._parent_fields(parent)

    @staticmethod
    def build_quantize_job_spec(
        quantize: TrainingHyperparameterQuantize,
        parent: ModelArtifact,
    ) -> Dict[str, Any]:
        return {
            "quantize": {
                "id": quantize.id,
                "method": quantize.method.value,
                "precision": quantize.precision.value,
                "calibration_samples": quantize.calibration_samples,
                "accuracy_drop_threshold": str(quantize.accuracy_drop_threshold),
                "qat_epochs": quantize.qat_epochs,
                "qat_learning_rate": quantize.qat_learning_rate,
            },
            "tier": ModelTier.EDGE.value,
            "role": ModelRole.STUDENT.value,
            "precision": quantize.precision.value,
        } | TrainJobSpec._parent_fields(parent)

    @staticmethod
    def _parent_fields(parent: ModelArtifact) -> Dict[str, Any]:
        return {
            "parent_id": parent.id,
            "parent_storage_path": parent.storage_path,
            "parent_architecture": parent.architecture,
            "parent_precision": parent.precision.value,
        }
