"""
Author: Sean Froning
Created Date: 8.29.2026
Main entrypoint for Fiery AI/ML API
"""

import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__)))

from fiery_python import logging
from fiery_python import ModelStorageServices
from .build_loaders import build_loaders
from .build_job import DistillPair, build_job
from .train_model import train_model
from .save_checkpoint import save_checkpoint
from .score_model import score_model
from .send_callback import send_callback

# Setup structured logging
logging.setup_structured_logging()
logger = logging.get_logger(__name__)

_MAX_TRAINING_ATTEMPTS = 2
_VIT_PARAMS = 22_100_000


def entrypoint(spec: Dict, architecture: str) -> Dict:
    import io
    import torch

    storage_path = None
    signature = None
    param_count = None
    metrics = None
    decision = None
    sidecar = None
    payload: bytes | dict | None = None
    for attempt in range(_MAX_TRAINING_ATTEMPTS):
        try:
            seed = spec["seed"]
            if seed is None or not isinstance(seed, int):
                raise RuntimeError("Missing seed from spec")
            _seed(seed)
            storage_path = (
                f"{spec['tier']}/{spec['role']}/{spec['session_id']}.safetensors"
            )
            loaders = build_loaders(spec)
            if not loaders or "train" not in loaders:
                raise RuntimeError("Failed to build dataset")
            model = build_job(spec)
            if model is None:
                raise RuntimeError("Failed to build job")
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model = model.to(device)
            model = train_model(model, loaders, spec)
            if model is None:
                raise RuntimeError("Failed to train model")
            metrics, decision = score_model(spec, model, loaders)
            if not metrics or not decision:
                raise RuntimeError("Failed to score model")
            if isinstance(model, DistillPair):
                architecture = (spec.get("distill") or {}).get(
                    "student_architecture"
                ) or architecture
                model = model.student
            cpu_model = model.cpu()
            sidecar = {
                "architecture": architecture,
                "stage": spec["stage"],
                "spec": spec,
                "decision": decision,
            }
            if spec.get("quantize"):
                example_shape = spec.get("example_shape")
                if (
                    not isinstance(example_shape, (list, tuple))
                    or len(example_shape) != 4
                ):
                    raise RuntimeError("Missing example_shape from spec")
                sidecar["example_shape"] = list(example_shape)
                example = torch.zeros(tuple(int(dim) for dim in example_shape))
                exported = torch.export.export(
                    cpu_model,
                    (example,),
                    dynamic_shapes=({0: torch.export.Dim("batch")},),
                )
                buffer = io.BytesIO()
                torch.export.save(exported, buffer)
                payload = buffer.getvalue()
                param_count = sum(param.numel() for param in cpu_model.parameters())
            elif spec.get("lora"):
                from peft import get_peft_model_state_dict

                sidecar["lora"] = spec["lora"]
                sidecar["base_model_id"] = spec["base_model_id"]
                sidecar["revision"] = spec["revision"]
                payload = get_peft_model_state_dict(cpu_model)
                param_count = _VIT_PARAMS + sum(
                    tensor.numel() for tensor in payload.values()
                )
            else:
                payload = cpu_model.state_dict()
                param_count = sum(param.numel() for param in cpu_model.parameters())
            ModelStorageServices.save_artifact(payload, sidecar, storage_path)
            signature = ModelStorageServices.head_hmac(storage_path)
            break
        except Exception as err:
            logger.warning(
                "modal_entrypoint_failed",
                spec=spec["session_id"],
                attempt=attempt,
                error=str(err),
            )
    if (
        storage_path
        and signature
        and sidecar
        and payload is not None
        and param_count
        and metrics
        and decision
    ):
        if isinstance(payload, bytes):
            weights_bytes = payload
        else:
            from safetensors.torch import save as save_safetensors

            weights_bytes = save_safetensors(payload)
        sidecar = save_checkpoint(
            spec,
            storage_path=storage_path,
            weights_bytes=weights_bytes,
            sidecar=sidecar,
        )
        if sidecar.get("hf_revision"):
            sidecar["weights_hmac"] = signature
            ModelStorageServices.put_sidecar(storage_path, sidecar)
        send_callback(
            spec,
            storage_path=storage_path,
            signature=signature,
            param_count=param_count,
            architecture=architecture,
            metrics=metrics,
            decision=decision,
            hf_repo_id=sidecar.get("hf_repo_id"),
            hf_revision=sidecar.get("hf_revision"),
        )
        return {
            "ok": True,
            "spec": spec["session_id"],
            "storage_path": storage_path,
        }
    else:
        return {
            "ok": False,
            "spec": spec["session_id"],
        }


def _seed(seed: int) -> None:
    import random
    import numpy as np
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
