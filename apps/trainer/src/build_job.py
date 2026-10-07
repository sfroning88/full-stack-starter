"""
Author: Sean Froning
Created Date: 8.29.2026
Build training frame
"""

import torch.nn as nn
from huggingface_hub import hf_hub_download
from peft import PeftModel
from typing import Callable, Dict, List, Optional
from fiery_python import ModelStorageServices, TrainingStage

_VIT_SNAPSHOT = "vit_small_patch16_224.augreg_in21k_ft_in1k"
_VIT_BASE_MODEL_ID = "timm/vit_small_patch16_224.augreg_in21k_ft_in1k"
_VIT_REVISION = "7e2c55630205e1266030f18370f4c6ed1a514b52"
_VIT_WEIGHTS = "model.safetensors"
_NUM_SEISMIC_CLASSES = 4
_TEACHER_ARCHITECTURE = "cnn_small"
_STUDENT_ARCHITECTURE = "cnn_tiny"


class SeismicCnn(nn.Module):

    def __init__(
        self, widths: tuple[int, ...], num_classes: int = _NUM_SEISMIC_CLASSES
    ):
        super().__init__()
        blocks: List[nn.Module] = []
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
        _kaiming(self)

    def forward(self, x):
        return self.head(self.features(x))


class DistillPair(nn.Module):

    def __init__(self, student: nn.Module, teacher: nn.Module):
        super().__init__()
        self.student = student
        self.teacher = teacher
        self.teacher.eval()
        for param in self.teacher.parameters():
            param.requires_grad = False

    def forward(self, x):
        return self.student(x)


_ARCHITECTURES: Dict[str, Callable[[], SeismicCnn]] = {
    _TEACHER_ARCHITECTURE: lambda: SeismicCnn(widths=(32, 64, 128)),
    _STUDENT_ARCHITECTURE: lambda: SeismicCnn(widths=(16, 32, 64)),
}


def build_job(spec: dict) -> Optional[nn.Module]:
    stage = spec["stage"]
    if not stage or not isinstance(stage, str):
        raise RuntimeError("Missing stage from spec")
    match stage:
        case TrainingStage.PRETRAIN.value:
            return _build_pretrain_job(spec)
        case TrainingStage.LORA.value:
            return _build_lora_job(spec)
        case TrainingStage.DISTILL.value:
            return _build_distill_job(spec)
        case TrainingStage.PRUNE.value:
            return _build_prune_job(spec)
        case TrainingStage.QUANTIZE.value:
            return _build_quantize_job(spec)
        case _:
            raise RuntimeError(f"Invalid stage from spec: {stage}")


def _build_pretrain_job(spec: dict) -> Optional[nn.Module]:
    return _make_cnn(_TEACHER_ARCHITECTURE)


def _build_lora_job(spec: dict) -> Optional[PeftModel]:
    import timm
    from peft import LoraConfig, get_peft_model

    lora = spec["lora"]
    targets = _peft_targets(lora["target_modules"])
    if not targets:
        raise RuntimeError("Empty LoRA target modules")
    base_model_id = spec.get("base_model_id")
    revision = spec.get("revision")
    if (
        not base_model_id
        or not revision
        or not isinstance(base_model_id, str)
        or not isinstance(revision, str)
    ):
        raise RuntimeError("Empty base_model_id and/or revision")
    hf_hub_download(
        repo_id=base_model_id,
        filename=_VIT_WEIGHTS,
        revision=revision,
    )
    backbone = timm.create_model(
        _VIT_SNAPSHOT,
        pretrained=True,
        num_classes=2,
    )
    config = LoraConfig(
        r=lora["rank"],
        lora_alpha=lora["alpha"],
        lora_dropout=lora["dropout"],
        target_modules=targets,
        modules_to_save=["head"],
        bias="none",
    )
    return get_peft_model(backbone, config)


def _build_distill_job(spec: dict) -> Optional[nn.Module]:
    distill = spec.get("distill") or {}
    student_name = distill.get("student_architecture", _STUDENT_ARCHITECTURE)
    student = _make_cnn(student_name)
    teacher = _load_parent(spec)
    teacher.eval()
    for param in teacher.parameters():
        param.requires_grad = False
    return DistillPair(student=student, teacher=teacher)


def _build_prune_job(spec: dict) -> Optional[nn.Module]:
    return _load_parent(spec)


def _build_quantize_job(spec: dict) -> Optional[nn.Module]:
    return _load_parent(spec)


def _make_cnn(architecture: str) -> SeismicCnn:
    factory = _ARCHITECTURES.get(architecture)
    if factory is None:
        raise RuntimeError(f"Unknown architecture: {architecture}")
    return factory()


def _load_parent(spec: dict) -> nn.Module:
    path = spec.get("parent_storage_path")
    architecture = spec.get("parent_architecture")
    if not path or not isinstance(path, str):
        raise RuntimeError("Missing parent_storage_path from spec")
    if not architecture or not isinstance(architecture, str):
        raise RuntimeError("Missing parent_architecture from spec")
    model = _make_cnn(architecture)
    state_dict, _sidecar = ModelStorageServices.load_artifact(path, is_weights=True)
    missing, unexpected = model.load_state_dict(state_dict, strict=True)
    if missing or unexpected:
        raise RuntimeError("Parent state_dict does not match architecture")
    return model


def _kaiming(module: nn.Module) -> None:
    for child in module.modules():
        if isinstance(child, nn.Conv2d):
            nn.init.kaiming_normal_(child.weight, mode="fan_out", nonlinearity="relu")
        elif isinstance(child, nn.Linear):
            nn.init.kaiming_uniform_(child.weight, nonlinearity="relu")
            if child.bias is not None:
                nn.init.zeros_(child.bias)
        elif isinstance(child, nn.BatchNorm2d):
            nn.init.ones_(child.weight)
            nn.init.zeros_(child.bias)


def _peft_targets(target_modules: dict) -> List[str]:
    targets = []
    if (
        target_modules.get("query")
        or target_modules.get("key")
        or target_modules.get("value")
    ):
        targets.append("qkv")
    if target_modules.get("output"):
        targets.append("proj")
    return targets
