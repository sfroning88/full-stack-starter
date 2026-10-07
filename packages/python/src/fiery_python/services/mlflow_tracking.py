"""
Author: Sean Froning
Created Date: 9.21.2026
mlflow process services and model tracking
"""

import mlflow
from typing import List, Optional
from ..core import config, logging
from ..constants import MLFLOW_REGISTERED_MODELS
from ..models import ModelArtifact, ModelMetric
from ..utils import MlflowUtils

logger = logging.get_logger(__name__)


class MlflowTrackingServices:
    """Model tracking across training sessions using mlflow"""

    @staticmethod
    def log_finished_run(artifact: ModelArtifact, metrics: List[ModelMetric]) -> str:
        tracking_uri = config.get("MLFLOW_TRACKING_URI")
        if not tracking_uri or not isinstance(tracking_uri, str):
            raise EnvironmentError("misconfigured MLFLOW_TRACKING_URI")
        experiment_name = config.get("MLFLOW_EXPERIMENT_NAME")
        if not experiment_name or not isinstance(experiment_name, str):
            experiment_name = "fiery-spirit"
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(experiment_name)
        registered_name = MLFLOW_REGISTERED_MODELS[(artifact.tier, artifact.role)]
        hf_repo_id = artifact.hf_repo_id or MlflowUtils.hf_repo_id(
            artifact.tier, artifact.role
        )
        with mlflow.start_run(run_name=artifact.session_id) as run:
            mlflow.log_params(
                {
                    "tier": artifact.tier.value,
                    "role": artifact.role.value,
                    "stage": artifact.stage.value,
                    "architecture": artifact.architecture,
                    "precision": artifact.precision.value,
                    "session_id": artifact.session_id,
                    "param_count": artifact.param_count,
                }
            )
            for metric in metrics:
                mlflow.log_metric(
                    f"{metric.split}_{metric.name}",
                    float(metric.value),
                )
            mlflow.set_tags(
                {
                    "storage_path": artifact.storage_path,
                    "signature": artifact.signature,
                    "hf_repo_id": hf_repo_id,
                    "hf_revision": artifact.hf_revision or "",
                    "parent_id": artifact.parent_id or "",
                }
            )
            mlflow.log_dict(
                {
                    "storage_path": artifact.storage_path,
                    "signature": artifact.signature,
                    "session_id": artifact.session_id,
                },
                "artifact.json",
            )
            mlflow.register_model(
                model_uri=f"runs:/{run.info.run_id}/artifact.json",
                name=registered_name,
            )
            return run.info.run_id

    @staticmethod
    def alias_production(name: str, version: Optional[str] = None) -> None:
        tracking_uri = config.get("MLFLOW_TRACKING_URI")
        if not tracking_uri or not isinstance(tracking_uri, str):
            raise EnvironmentError("misconfigured MLFLOW_TRACKING_URI")
        mlflow.set_tracking_uri(tracking_uri)
        client = mlflow.MlflowClient()
        if version is None:
            versions = client.search_model_versions(f"name='{name}'")
            if not versions:
                raise RuntimeError(f"no registered versions for {name}")
            version = str(max(int(item.version) for item in versions))
        client.set_registered_model_alias(name, "production", version)

    @staticmethod
    def registered_version_for_run(name: str, run_id: str) -> str:
        tracking_uri = config.get("MLFLOW_TRACKING_URI")
        if not tracking_uri or not isinstance(tracking_uri, str):
            raise EnvironmentError("misconfigured MLFLOW_TRACKING_URI")
        mlflow.set_tracking_uri(tracking_uri)
        client = mlflow.MlflowClient()
        versions = client.search_model_versions(
            filter_string=f"name = '{name}' AND run_id = '{run_id}'"
        )
        if not versions:
            raise RuntimeError(f"no registered version for {name} run_id={run_id}")
        if len(versions) > 1:
            return str(max(int(ver.version) for ver in versions))
        return str(versions[0].version)
