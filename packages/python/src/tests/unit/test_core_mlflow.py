"""
Author: Sean Froning
Created Date: 10.7.2026
Unit tests for the process-local MLflow client
"""

from unittest.mock import MagicMock, patch

import pytest
from my_python import mlflow


@pytest.fixture(autouse=True)
def _reset_mlflow_client():
    mlflow.reset()
    yield
    mlflow.reset()


def test_get_client_requires_tracking_uri(monkeypatch):
    monkeypatch.delenv("MLFLOW_TRACKING_URI", raising=False)

    with pytest.raises(EnvironmentError, match="MLFLOW_TRACKING_URI"):
        mlflow.get_client()


def test_get_client_sets_tracking_and_experiment(monkeypatch):
    monkeypatch.setenv("MLFLOW_TRACKING_URI", "http://mlflow.example")
    monkeypatch.setenv("MLFLOW_EXPERIMENT_NAME", "pipelines")
    client = MagicMock()

    with (
        patch("my_python.core.mlflow.MlflowClient", return_value=client) as ctor,
        patch("my_python.core.mlflow._mlflow.set_tracking_uri") as set_uri,
        patch("my_python.core.mlflow._mlflow.set_experiment") as set_exp,
    ):
        assert mlflow.get_client() is client
        assert mlflow.get_client() is client

    set_uri.assert_called_once_with("http://mlflow.example")
    set_exp.assert_called_once_with("pipelines")
    ctor.assert_called_once_with(tracking_uri="http://mlflow.example")


def test_experiment_name_defaults(monkeypatch):
    monkeypatch.setenv("MLFLOW_TRACKING_URI", "http://mlflow.example")
    monkeypatch.delenv("MLFLOW_EXPERIMENT_NAME", raising=False)

    with (
        patch("my_python.core.mlflow.MlflowClient", return_value=MagicMock()),
        patch("my_python.core.mlflow._mlflow.set_tracking_uri"),
        patch("my_python.core.mlflow._mlflow.set_experiment") as set_exp,
    ):
        mlflow.get_client()

    set_exp.assert_called_once_with("default")


def test_set_alias_uses_latest_version():
    client = MagicMock()
    client.search_model_versions.return_value = [
        MagicMock(version="2"),
        MagicMock(version="7"),
    ]
    with patch.object(mlflow, "get_client", return_value=client):
        mlflow.set_alias("screen", "production")

    client.set_registered_model_alias.assert_called_once_with(
        "screen", "production", "7"
    )


def test_set_alias_raises_when_unregistered():
    client = MagicMock()
    client.search_model_versions.return_value = []
    with patch.object(mlflow, "get_client", return_value=client):
        with pytest.raises(RuntimeError, match="no registered versions"):
            mlflow.set_alias("screen", "production")


def test_registered_version_for_run():
    client = MagicMock()
    client.search_model_versions.return_value = [
        MagicMock(version="3"),
        MagicMock(version="4"),
    ]
    with patch.object(mlflow, "get_client", return_value=client):
        assert mlflow.registered_version_for_run("screen", "run-1") == "4"

    client.search_model_versions.assert_called_once_with(
        filter_string="name = 'screen' AND run_id = 'run-1'"
    )


def test_register_model_uses_run_uri():
    with (
        patch.object(mlflow, "get_client", return_value=MagicMock()),
        patch("my_python.core.mlflow._mlflow.register_model", return_value="ok") as reg,
    ):
        assert mlflow.register_model("run-1", "artifact.json", "screen") == "ok"

    reg.assert_called_once_with(
        model_uri="runs:/run-1/artifact.json",
        name="screen",
    )


def test_log_metrics_casts_values():
    with (
        patch.object(mlflow, "get_client", return_value=MagicMock()) as get_client,
        patch("my_python.core.mlflow._mlflow.log_metrics") as log_metrics,
    ):
        mlflow.log_metrics({"loss": 1})

    get_client.assert_called_once()
    log_metrics.assert_called_once_with({"loss": 1.0})
