"""
Author: Sean Froning
Created Date: 10.7.2026
Process-local MLflow tracking client
"""

from typing import Any, Optional
import mlflow as _mlflow
from mlflow.tracking import MlflowClient
from .config import config
from ..resources import SyncLazyResource


class _MLFlow:
    """Lazy MLflow client bound to tracking URI and experiment env"""

    def __init__(self) -> None:
        self._client = SyncLazyResource(self._build_client)

    def _tracking_uri(self) -> str:
        tracking_uri = config.get("MLFLOW_TRACKING_URI")
        if not tracking_uri or not isinstance(tracking_uri, str):
            raise EnvironmentError("misconfigured MLFLOW_TRACKING_URI")
        return tracking_uri

    def _experiment_name(self) -> str:
        experiment_name = config.get("MLFLOW_EXPERIMENT_NAME")
        if not experiment_name or not isinstance(experiment_name, str):
            return "default"
        return experiment_name

    def _build_client(self) -> MlflowClient:
        uri = self._tracking_uri()
        _mlflow.set_tracking_uri(uri)
        _mlflow.set_experiment(self._experiment_name())
        return MlflowClient(tracking_uri=uri)

    def get_client(self) -> MlflowClient:
        """Lazy-load shared tracking client (cached per worker process)"""
        return self._client.get()

    def reset(self) -> None:
        """Drop the cached client so a forked child rebuilds its own"""
        self._client.reset()

    def start_run(self, run_name: Optional[str] = None, **kwargs: Any):
        """Open a run after tracking URI and experiment are configured"""
        self.get_client()
        return _mlflow.start_run(run_name=run_name, **kwargs)

    def log_params(self, params: dict[str, Any]) -> None:
        _mlflow.log_params(params)

    def log_metrics(self, metrics: dict[str, float]) -> None:
        _mlflow.log_metrics({key: float(value) for key, value in metrics.items()})

    def set_tags(self, tags: dict[str, Any]) -> None:
        _mlflow.set_tags(
            {key: "" if value is None else str(value) for key, value in tags.items()}
        )

    def log_dict(self, payload: dict[str, Any], artifact_file: str) -> None:
        _mlflow.log_dict(payload, artifact_file)

    def register_model(self, run_id: str, artifact_path: str, name: str) -> Any:
        """Register an artifact path from a finished run under a model name"""
        self.get_client()
        return _mlflow.register_model(
            model_uri=f"runs:/{run_id}/{artifact_path}",
            name=name,
        )

    def set_alias(self, name: str, alias: str, version: Optional[str] = None) -> None:
        """Point an alias at a version, or the latest version when omitted"""
        client = self.get_client()
        if version is None:
            versions = client.search_model_versions(f"name='{name}'")
            if not versions:
                raise RuntimeError(f"no registered versions for {name}")
            version = str(max(int(item.version) for item in versions))
        client.set_registered_model_alias(name, alias, version)

    def registered_version_for_run(self, name: str, run_id: str) -> str:
        """Return the registered version created by a run"""
        client = self.get_client()
        versions = client.search_model_versions(
            filter_string=f"name = '{name}' AND run_id = '{run_id}'"
        )
        if not versions:
            raise RuntimeError(f"no registered version for {name} run_id={run_id}")
        if len(versions) > 1:
            return str(max(int(ver.version) for ver in versions))
        return str(versions[0].version)


mlflow = _MLFlow()
