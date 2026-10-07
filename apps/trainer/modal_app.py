"""
Author: Sean Froning
Created Date: 8.29.2026
Modal app deployment
"""

import modal
from typing import Dict

app = modal.App("fiery-trainer")

secrets = [modal.Secret.from_name("Fiery-Environment")]


def _download_vit_small() -> None:
    import timm
    from huggingface_hub import hf_hub_download

    _VIT_SNAPSHOT = "vit_small_patch16_224.augreg_in21k_ft_in1k"
    _VIT_BASE_MODEL_ID = "timm/vit_small_patch16_224.augreg_in21k_ft_in1k"
    _VIT_REVISION = "7e2c55630205e1266030f18370f4c6ed1a514b52"
    _VIT_WEIGHTS = "model.safetensors"

    hf_hub_download(
        repo_id=_VIT_BASE_MODEL_ID,
        filename=_VIT_WEIGHTS,
        revision=_VIT_REVISION,
    )
    timm.create_model(
        _VIT_SNAPSHOT,
        pretrained=True,
        num_classes=2,
    )


image = (
    modal.Image.debian_slim(python_version="3.13")
    .uv_pip_install(
        "safetensors==0.8.0",
        "mlflow[db]==3.16.1",
        "huggingface_hub==1.16.1",
        "torch==2.13.0",
        "torchao==0.18.0",
        "timm==1.0.28",
        "peft==0.20.0",
        "webdataset==1.0.2",
    )
    .run_function(_download_vit_small, secrets=secrets)
    .add_local_dir(
        "../../packages/python",
        remote_path="/opt/packages/python",
        copy=True,
        ignore=[
            ".venv",
            ".venv/**",
            "**/__pycache__",
            "**/__pycache__/**",
            "**/*.pyc",
            "**/*.egg-info",
            "**/*.egg-info/**",
        ],
    )
    .run_commands("uv pip install --system -e /opt/packages/python")
    .add_local_python_source("src")
)


@app.function(image=image, gpu="T4", timeout=7200, secrets=secrets)
def pretrain_teacher(spec: Dict) -> Dict:
    from src.entrypoint import entrypoint

    return entrypoint(spec, architecture="cnn_small")


@app.function(image=image, gpu="T4", timeout=3600, secrets=secrets)
def lora_screener(spec: Dict) -> Dict:
    from src.entrypoint import entrypoint

    _VIT_SNAPSHOT = "vit_small_patch16_224.augreg_in21k_ft_in1k"

    return entrypoint(spec, architecture=_VIT_SNAPSHOT)


@app.function(image=image, gpu="T4", timeout=3600, secrets=secrets)
def distill_student(spec: Dict) -> Dict:
    from src.entrypoint import entrypoint

    return entrypoint(spec, architecture="cnn_tiny")


@app.function(image=image, gpu="T4", timeout=3600, secrets=secrets)
def prune_student(spec: Dict) -> Dict:
    from src.entrypoint import entrypoint

    return entrypoint(spec, architecture="cnn_tiny")


@app.function(image=image, cpu=4, memory=8192, timeout=5400, secrets=secrets)
def quantize_student(spec: Dict) -> Dict:
    from src.entrypoint import entrypoint

    return entrypoint(spec, architecture="cnn_tiny")


@app.function(image=image, secrets=secrets, timeout=60)
def smoke(_spec: Dict) -> Dict:
    return {"ok": True}


@app.local_entrypoint()
def main() -> None:
    print(smoke.remote({}))
