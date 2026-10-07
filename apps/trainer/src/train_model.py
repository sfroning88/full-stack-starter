"""
Author: Sean Froning
Created Date: 8.29.2026
Train corresponding model
"""

import torch.nn as nn
from torch import Tensor
from torch.utils.data import DataLoader
from typing import Dict
from fiery_python import TrainingStage

_NUM_SEISMIC_CLASSES = 4


def train_model(
    model: nn.Module, loaders: Dict[str, DataLoader], spec: dict
) -> nn.Module:
    stage = spec["stage"]
    if not stage or not isinstance(stage, str):
        raise RuntimeError("Missing stage from spec")
    match stage:
        case TrainingStage.PRETRAIN.value:
            return _train_pretrain_model(model, loaders, spec)
        case TrainingStage.LORA.value:
            return _train_lora_model(model, loaders, spec)
        case TrainingStage.DISTILL.value:
            return _train_distill_model(model, loaders, spec)
        case TrainingStage.PRUNE.value:
            return _train_prune_model(model, loaders, spec)
        case TrainingStage.QUANTIZE.value:
            return _train_quantize_model(model, loaders, spec)
        case _:
            raise RuntimeError(f"Invalid stage from spec: {stage}")


def _train_pretrain_model(
    model: nn.Module, loaders: Dict[str, DataLoader], spec: dict
) -> nn.Module:
    pretrain = spec.get("pretrain") or {}
    loader = loaders["train"]
    device = next(model.parameters()).device
    weights = _class_weights(loader.dataset.tensors[1].to(device), _NUM_SEISMIC_CLASSES)
    optimizer = _optimizer(
        model,
        pretrain["optimizer"],
        pretrain["learning_rate"],
        pretrain["weight_decay"],
    )
    scheduler = _lr_scheduler(optimizer, pretrain["lr_schedule"], pretrain["epochs"])
    loss_fn = nn.CrossEntropyLoss(weight=weights)
    model.train()
    for _ in range(pretrain["epochs"]):
        _epoch(model, loader, optimizer, loss_fn, device)
        scheduler.step()
    return model


def _train_lora_model(
    model: nn.Module, loaders: Dict[str, DataLoader], spec: dict
) -> nn.Module:
    import torch

    lora = spec["lora"]
    loader = loaders["train"]
    device = next(model.parameters()).device
    model.train()
    optimizer = torch.optim.AdamW(
        (param for param in model.parameters() if param.requires_grad),
        lr=lora["learning_rate"],
    )
    loss_fn = nn.CrossEntropyLoss()
    for _ in range(lora["epochs"]):
        for images, targets in loader:
            images = images.to(device)
            targets = targets.to(device)
            optimizer.zero_grad()
            loss = loss_fn(model(images), targets)
            loss.backward()
            optimizer.step()
    return model


def _train_distill_model(
    model: nn.Module, loaders: Dict[str, DataLoader], spec: dict
) -> nn.Module:
    import torch
    import torch.nn.functional as F

    distill = spec.get("distill") or {}
    loader = loaders["train"]
    student = model.student
    teacher = model.teacher
    device = next(student.parameters()).device
    teacher.to(device)
    teacher.eval()
    temperature = float(distill["temperature"])
    alpha = float(distill["alpha"])
    weights = _class_weights(loader.dataset.tensors[1].to(device), _NUM_SEISMIC_CLASSES)
    optimizer = torch.optim.AdamW(
        (param for param in student.parameters() if param.requires_grad),
        lr=distill["learning_rate"],
    )
    ce_fn = nn.CrossEntropyLoss(weight=weights)
    student.train()
    for _ in range(distill["epochs"]):
        for features, targets in loader:
            features = features.to(device)
            targets = targets.to(device)
            optimizer.zero_grad()
            student_logits = student(features)
            with torch.no_grad():
                teacher_logits = teacher(features)
            soft = F.kl_div(
                F.log_softmax(student_logits / temperature, dim=1),
                F.softmax(teacher_logits / temperature, dim=1),
                reduction="batchmean",
            ) * (temperature**2)
            hard = ce_fn(student_logits, targets)
            loss = alpha * soft + (1.0 - alpha) * hard
            loss.backward()
            optimizer.step()
    return model


def _train_prune_model(
    model: nn.Module, loaders: Dict[str, DataLoader], spec: dict
) -> nn.Module:
    import torch
    from torch.nn.utils import prune
    from fiery_python import TrainingSparsitySchedule

    prune_spec = spec.get("prune") or {}
    loader = loaders["train"]
    device = next(model.parameters()).device
    target = float(prune_spec["target_sparsity"])
    iterations = int(prune_spec["iterations"])
    finetune_epochs = int(prune_spec["finetune_epochs_per_iter"])
    schedule = prune_spec["sparsity_schedule"]
    criterion = prune_spec["pruning_criterion"]
    convs = [
        (module, "weight")
        for module in model.modules()
        if isinstance(module, nn.Conv2d)
    ]
    if not convs:
        raise RuntimeError("No Conv2d modules to prune")
    method = _prune_method(criterion)
    weights = _class_weights(loader.dataset.tensors[1].to(device), _NUM_SEISMIC_CLASSES)
    loss_fn = nn.CrossEntropyLoss(weight=weights)
    optimizer = torch.optim.AdamW(
        (param for param in model.parameters() if param.requires_grad),
        lr=1e-4,
    )
    previous = 0.0
    steps = 1 if schedule == TrainingSparsitySchedule.ONE_SHOT.value else iterations
    for index in range(1, steps + 1):
        desired = _sparsity_at(index, steps, target, schedule)
        remaining = 1.0 - previous
        if remaining <= 0:
            break
        amount = min(max((desired - previous) / remaining, 0.0), 1.0)
        if amount > 0:
            prune.global_unstructured(convs, pruning_method=method, amount=amount)
        previous = desired
        model.train()
        for _ in range(finetune_epochs):
            _epoch(model, loader, optimizer, loss_fn, device)
    for module, name in convs:
        prune.remove(module, name)
    return model


def _train_quantize_model(
    model: nn.Module, loaders: Dict[str, DataLoader], spec: dict
) -> nn.Module:
    import torch
    from torchao.quantization.pt2e import allow_exported_model_train_eval
    from torchao.quantization.pt2e.quantize_pt2e import (
        prepare_pt2e,
        prepare_qat_pt2e,
        convert_pt2e,
    )
    from fiery_python import TrainingQuantizeMethod

    quantize = spec.get("quantize") or {}
    method = quantize.get("method")
    calibrate = loaders.get("calibrate")
    train = loaders.get("train")
    if calibrate is None or train is None:
        raise RuntimeError("Missing calibrate or train loader")
    example, _targets = next(iter(calibrate))
    example = example.cpu()
    spec["example_shape"] = list(example.shape)
    model = model.cpu()
    exported = torch.export.export(
        model,
        (example,),
        dynamic_shapes=({0: torch.export.Dim("batch")},),
    ).module()
    quantizer = _x86_quantizer()
    if method == TrainingQuantizeMethod.PTQ.value:
        prepared = prepare_pt2e(exported, quantizer)
        allow_exported_model_train_eval(prepared)
        prepared.eval()
        with torch.no_grad():
            for features, _targets in calibrate:
                prepared(features.cpu())
        converted = convert_pt2e(prepared)
        allow_exported_model_train_eval(converted)
        return converted
    elif method == TrainingQuantizeMethod.QAT.value:
        prepared = prepare_qat_pt2e(exported, quantizer)
        allow_exported_model_train_eval(prepared)
        prepared.train()
        optimizer = torch.optim.AdamW(
            (param for param in prepared.parameters() if param.requires_grad),
            lr=quantize["qat_learning_rate"],
        )
        loss_fn = nn.CrossEntropyLoss()
        for _ in range(quantize["qat_epochs"]):
            for features, targets in train:
                features = features.cpu()
                targets = targets.cpu()
                optimizer.zero_grad()
                loss = loss_fn(prepared(features), targets)
                loss.backward()
                optimizer.step()
        prepared.eval()
        converted = convert_pt2e(prepared)
        allow_exported_model_train_eval(converted)
        return converted
    raise RuntimeError("Unsupported quantize method")


def _epoch(model, loader, optimizer, loss_fn, device) -> None:
    for features, targets in loader:
        features = features.to(device)
        targets = targets.to(device)
        optimizer.zero_grad()
        loss = loss_fn(model(features), targets)
        loss.backward()
        optimizer.step()


def _optimizer(model, name: str, lr: float, weight_decay) -> object:
    import torch
    from fiery_python import TrainingOptimizer

    params = (param for param in model.parameters() if param.requires_grad)
    decay = float(weight_decay)
    if name == TrainingOptimizer.ADAMW.value:
        return torch.optim.AdamW(params, lr=lr, weight_decay=decay)
    if name == TrainingOptimizer.ADAM.value:
        return torch.optim.Adam(params, lr=lr, weight_decay=decay)
    if name == TrainingOptimizer.SGD.value:
        return torch.optim.SGD(params, lr=lr, weight_decay=decay, momentum=0.9)
    if name == TrainingOptimizer.RMSPROP.value:
        return torch.optim.RMSprop(params, lr=lr, weight_decay=decay)
    raise RuntimeError(f"Unsupported optimizer: {name}")


def _lr_scheduler(optimizer, name: str, epochs: int):
    import torch
    from fiery_python import TrainingRateSchedule

    if name == TrainingRateSchedule.CONSTANT.value:
        return torch.optim.lr_scheduler.ConstantLR(optimizer, factor=1.0)
    if name == TrainingRateSchedule.COSINE.value:
        return torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    if name == TrainingRateSchedule.STEP.value:
        return torch.optim.lr_scheduler.StepLR(optimizer, step_size=max(epochs // 3, 1))
    if name in (
        TrainingRateSchedule.LINEAR.value,
        TrainingRateSchedule.WARMUP_COSINE.value,
    ):
        return torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    raise RuntimeError(f"Unsupported lr_schedule: {name}")


def _sparsity_at(index: int, steps: int, target: float, schedule: str) -> float:
    from fiery_python import TrainingSparsitySchedule

    if schedule == TrainingSparsitySchedule.ONE_SHOT.value or steps <= 1:
        return target
    t = index / steps
    if schedule == TrainingSparsitySchedule.LINEAR.value:
        return target * t
    if schedule == TrainingSparsitySchedule.CUBIC.value:
        return target * (t**3)
    raise RuntimeError(f"Unsupported sparsity_schedule: {schedule}")


def _prune_method(criterion: str):
    from torch.nn.utils import prune
    from fiery_python import TrainingPruningCriterion

    if criterion == TrainingPruningCriterion.L1_MAGNITUDE.value:
        return prune.L1Unstructured
    if criterion == TrainingPruningCriterion.RANDOM.value:
        return prune.RandomUnstructured
    if criterion == TrainingPruningCriterion.L2_MAGNITUDE.value:
        return prune.L1Unstructured
    raise RuntimeError(f"Unsupported pruning_criterion: {criterion}")


def _x86_quantizer():
    from torchao.quantization.pt2e.quantizer.x86_inductor_quantizer import (
        X86InductorQuantizer,
        get_default_x86_inductor_quantization_config,
    )

    quantizer = X86InductorQuantizer()
    quantizer.set_global(get_default_x86_inductor_quantization_config())
    return quantizer


def _class_weights(targets: Tensor, num_classes: int) -> Tensor:
    import torch

    counts = torch.bincount(targets, minlength=num_classes).float()
    counts = counts.clamp(min=1.0)
    weights = counts.sum() / (num_classes * counts)
    return weights
