"""
Author: Sean Froning
Created Date: 10.7.2026
Modal app deployment
"""

import modal
from pathlib import Path
from typing import Dict

app = modal.App("my-project")

secrets = [modal.Secret.from_name("My-Environment")]


image = (
    modal.Image.debian_slim(python_version="3.13")
    .uv_pip_install(
        "mlflow[db]==3.16.1",
        "huggingface_hub==1.16.1",
    )
    .add_local_dir(
        str(Path(__file__).resolve().parents[2] / "packages" / "python"),
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


@app.function(image=image, secrets=secrets, timeout=60)
def smoke(_spec: Dict) -> Dict:
    from src.entrypoint import entrypoint

    return entrypoint({})


@app.local_entrypoint()
def main() -> None:
    print(smoke.remote({}))
