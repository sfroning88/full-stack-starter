"""
Author: Sean Froning
Created Date: 8.20.2026
Inference-side cache of trained models
"""

import io
import threading
import timm
import torch
import torch.nn as nn
from decimal import Decimal
from huggingface_hub import hf_hub_download
from peft import LoraConfig, get_peft_model, set_peft_model_state_dict
from safetensors.torch import load
from timm.models import load_checkpoint
from typing import Any, Dict, Optional, Tuple
from fiery_python import db_pool, logging, SyncLazyResource
from fiery_python import (
    PoolFetch,
    MODEL_REGISTRY_SLOTS,
    ModelTier,
    ModelRole,
    TrainingStage,
    TrainingPrecision,
    ModelStorageServices,
)
from .models import LoadedModel, ArtifactRegistry
from .queries.select_promoted_artifact import QUERY as SELECT_PROMOTED_ARTIFACT

logger = logging.get_logger(__name__)

_VIT_SNAPSHOT = "vit_small_patch16_224.augreg_in21k_ft_in1k"
_VIT_BASE_MODEL_ID = "timm/vit_small_patch16_224.augreg_in21k_ft_in1k"
_VIT_REVISION = "7e2c55630205e1266030f18370f4c6ed1a514b52"
_VIT_WEIGHTS = "model.safetensors"
_CNN_WIDTHS = {
    TrainingStage.PRETRAIN: (32, 64, 128),
    TrainingStage.DISTILL: (16, 32, 64),
    TrainingStage.PRUNE: (16, 32, 64),
    TrainingStage.QUANTIZE: (16, 32, 64),
}
_NUM_SEISMIC_CLASSES = 4


class SeismicCnn(nn.Module):
    def __init__(
        self, widths: tuple[int, ...], num_classes: int = _NUM_SEISMIC_CLASSES
    ):
        super().__init__()
        blocks: list[nn.Module] = []
        in_ch = 1
        for width in widths:
            blocks.extend(
                [
                    nn.Conv2d(in_ch, width, kernel_size=3, padding=1, bias=False),
                    nn.BatchNorm2d(width),
                    nn.ReLU(inplace=True),
                    nn.MaxPool2d(2),
                ]
            )
            in_ch = width
        self.features = nn.Sequential(*blocks)
        self.head = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(in_ch, num_classes),
        )

    def forward(self, x):
        return self.head(self.features(x))


class _RegistrySlot:
    """Per-key cache slot with lazy empty state and explicit invalidation"""

    def __init__(self) -> None:
        self._state = SyncLazyResource(self._empty_registry)

    @staticmethod
    def _empty_registry() -> ArtifactRegistry:
        return ArtifactRegistry(
            model=None,
            metadata=None,
            artifact_id=None,
        )

    def get(self) -> ArtifactRegistry:
        return self._state.get()

    def reset(self) -> None:
        self._state.reset()


class _ModelRegistry:
    """In-memory cache of trained model keyed by (tier, role)"""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._slots: Dict[Tuple[ModelTier, ModelRole], _RegistrySlot] = {
            (tier, role): _RegistrySlot() for tier, role in MODEL_REGISTRY_SLOTS
        }

    def _slot(self, key: Tuple[ModelTier, ModelRole]) -> _RegistrySlot:
        slot = self._slots.get(key)
        if slot is None:
            slot = _RegistrySlot()
            self._slots[key] = slot
        return slot

    def load(
        self,
        key: Tuple[ModelTier, ModelRole],
        force: bool = False,
    ) -> None:
        """Attempt to pull fresh model into the cache"""
        try:
            tier, role = key
            artifact_id = None
            row = self._fetch_promoted_artifact(key)
            if row:
                artifact_id = str(row.get("id")) if row.get("id") else None
        except Exception as err:
            logger.error("registry_lookup_failed", error=str(err))
            raise RuntimeError(f"Model registry lookup failed: {str(err)}")

        if not row or not artifact_id:
            logger.info("registry_no_promoted_artifact")
            with self._lock:
                self._slot(key).reset()
            return

        with self._lock:
            slot = self._slot(key)
            reg = slot.get()
            already_current = artifact_id == reg.artifact_id
            if not force and already_current:
                logger.debug("registry_already_current", artifact=artifact_id)
                return

            entry, model = self._load_model_entry(row, artifact_id)
            if not entry or not model:
                logger.warning(
                    "registry_load_failed_keeping_cached",
                    tier=tier.value,
                    role=role.value,
                    candidate=artifact_id,
                    cached=reg.artifact_id,
                )
                raise RuntimeError(
                    f"Model artifact {artifact_id} failed to materialize"
                )

            slot.reset()
            reg = slot.get()
            reg.model = model
            reg.metadata = entry
            reg.artifact_id = artifact_id
            logger.info(
                "registry_loaded",
                artifact=artifact_id,
                tier=tier.value,
                role=role.value,
            )

    def get(self, key: Tuple[ModelTier, ModelRole]) -> nn.Module:
        """Return cached model artifact or raise if missing"""
        with self._lock:
            artifact = self._slot(key).get().model
        if artifact is None:
            tier, role = key
            raise RuntimeError(
                f"Model artifact not loaded for ({tier.value}, {role.value})"
            )
        return artifact

    def get_metadata(self, key: Tuple[ModelTier, ModelRole]) -> Dict[str, Any]:
        """Return cached metadata"""
        with self._lock:
            entry = self._slot(key).get().metadata
        return entry.model_dump() if entry else {}

    def is_ready(self, key: Tuple[ModelTier, ModelRole]) -> bool:
        """True if a promoted artifact is currently cached"""
        with self._lock:
            return self._slot(key).get().model is not None

    def reset(self) -> None:
        """Drop all cached slots so the next load rebuilds from the database"""
        with self._lock:
            for slot in self._slots.values():
                slot.reset()

    @staticmethod
    def materialize(sidecar: dict) -> nn.Module:
        try:
            stage = (
                TrainingStage(sidecar.get("stage"))
                if (sidecar.get("stage") and isinstance(sidecar.get("stage"), str))
                else None
            )
        except ValueError:
            stage = None
        if not stage:
            raise RuntimeError("Stage from sidecar missing or malformed")
        if stage is TrainingStage.LORA:
            return _ModelRegistry._materialize_screener(sidecar)
        else:
            return _ModelRegistry._materialize_cnn(stage)

    @staticmethod
    def _materialize_screener(sidecar: dict) -> nn.Module:
        lora = sidecar.get("lora")
        if not lora:
            raise RuntimeError("sidecar missing lora")
        modules = lora.get("target_modules") or {}
        targets = []
        if modules.get("query") or modules.get("key") or modules.get("value"):
            targets.append("qkv")
        if modules.get("output"):
            targets.append("proj")
        if not targets:
            raise RuntimeError("Empty LoRA target modules")
        base_model_id = sidecar.get("base_model_id")
        revision = sidecar.get("revision")
        if (
            not base_model_id
            or not revision
            or not isinstance(base_model_id, str)
            or not isinstance(revision, str)
        ):
            raise RuntimeError("Empty base_model_id and/or revision")
        weights_path = hf_hub_download(
            repo_id=base_model_id,
            filename=_VIT_WEIGHTS,
            revision=revision,
            local_files_only=True,
        )
        backbone = timm.create_model(
            _VIT_SNAPSHOT,
            pretrained=False,
            num_classes=1000,
        )
        load_checkpoint(backbone, weights_path, strict=False)
        backbone.reset_classifier(num_classes=2)
        config = LoraConfig(
            r=lora["rank"],
            lora_alpha=lora["alpha"],
            lora_dropout=lora["dropout"],
            target_modules=targets,
            modules_to_save=["head"],
            bias="none",
        )
        return get_peft_model(backbone, config)

    @staticmethod
    def _materialize_cnn(stage: TrainingStage) -> nn.Module:
        return SeismicCnn(widths=_CNN_WIDTHS[stage])

    def _load_model_entry(
        self, row: Dict[str, Any], artifact_id: str
    ) -> tuple[Optional[LoadedModel], Optional[nn.Module]]:
        """Load one S3 artifact; returns (LoadedModel, artifact) or (None, None) on failure"""
        storage_path = str(row.get("storage_path")) if row.get("storage_path") else None
        if not storage_path:
            logger.error("missing required storage_path")
            return None, None
        try:
            payload, sidecar = ModelStorageServices.load_artifact(
                storage_path, is_body=True
            )
        except Exception as err:
            logger.error(
                "registry_load_failed",
                key=storage_path,
                error=str(err),
            )
            return None, None
        try:
            stage = (
                TrainingStage(sidecar.get("stage"))
                if (sidecar.get("stage") and isinstance(sidecar.get("stage"), str))
                else None
            )
            if not stage:
                raise ValueError
            if stage is TrainingStage.QUANTIZE:
                model = torch.export.load(io.BytesIO(payload)).module()
            else:
                state_dict = payload if isinstance(payload, dict) else load(payload)
                model = self.materialize(sidecar)
                if stage is TrainingStage.LORA:
                    set_peft_model_state_dict(model, state_dict)
                else:
                    model.load_state_dict(state_dict, strict=True)
                model.eval()
        except ValueError:
            logger.error(
                "registry_materialize_failed",
                key=storage_path,
                error="Stage from sidecar missing or malformed",
            )
            return None, None
        except Exception as err:
            logger.error(
                "registry_materialize_failed",
                key=storage_path,
                error=str(err),
            )
            return None, None
        decision = sidecar.get("decision") or {}
        entry = LoadedModel(
            artifact_id=artifact_id,
            tier=ModelTier(row.get("tier")),
            role=ModelRole(row.get("role")),
            stage=TrainingStage(row.get("stage")),
            precision=TrainingPrecision(row.get("precision")),
            architecture=str(row.get("architecture")),
            param_count=int(row.get("param_count") or 0),
            sparsity=Decimal(str(row.get("sparsity") or "0")),
            storage_path=str(row.get("storage_path")),
            signature=str(row.get("signature")),
            signed_at=row.get("signed_at"),
            promoted=bool(row.get("promoted")),
            promoted_at=row.get("promoted_at"),
            mlflow_run_id=row.get("mlflow_run_id"),
            hf_repo_id=row.get("hf_repo_id"),
            hf_revision=row.get("hf_revision"),
            session_id=str(row.get("session_id")),
            parent_id=str(row.get("parent_id")) if row.get("parent_id") else None,
            preprocessing=decision,
        )
        return entry, model

    @staticmethod
    def _fetch_promoted_artifact(
        key: Tuple[ModelTier, ModelRole],
    ) -> Optional[Dict[str, Any]]:
        """Return the promoted artifact or None"""
        tier, role = key
        with db_pool.get_cursor() as cursor:
            query = SELECT_PROMOTED_ARTIFACT.as_string(cursor)
        return db_pool.run(
            query,
            (tier.value, role.value),
            fetch=PoolFetch.ONE,
        )


model_registry = _ModelRegistry()
