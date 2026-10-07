"""
Author: Sean Froning
Created Date: 9.21.2026
Unit tests for MlflowTrackingServices
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fiery_python import (
    ModelArtifact,
    ModelMetric,
    ModelMetricName,
    ModelRole,
    ModelTier,
    MlflowTrackingServices,
    TrainingPrecision,
    TrainingSplit,
    TrainingStage,
)

_MLFLOW = "fiery_python.services.mlflow_tracking.mlflow"
_CONFIG = "fiery_python.services.mlflow_tracking.config.get"
_MLFLOW_UTILS = "fiery_python.services.mlflow_tracking.MlflowUtils"
_RUN_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
_TRACKING_URI = "http://mlflow.example"


def _artifact(**overrides) -> ModelArtifact:
    base = dict(
        id="11111111-1111-1111-1111-111111111111",
        tier=ModelTier.CLOUD,
        role=ModelRole.SCREENER,
        stage=TrainingStage.LORA,
        precision=TrainingPrecision.FP32,
        architecture="vit-small",
        param_count=22000000,
        sparsity=Decimal("0"),
        storage_path="cloud/screener/art-1.pkl",
        signature="a" * 64,
        signed_at=datetime(2026, 9, 21, tzinfo=timezone.utc),
        promoted=False,
        session_id="22222222-2222-2222-2222-222222222222",
        hf_repo_id="org/Fiery-Screener",
    )
    base.update(overrides)
    return ModelArtifact(**base)


def _metric(
    name: ModelMetricName = ModelMetricName.RECALL,
    split: TrainingSplit = TrainingSplit.TEST,
    value: Decimal = Decimal("0.910"),
) -> ModelMetric:
    return ModelMetric(
        name=name,
        split=split,
        value=value,
        artifact_id="11111111-1111-1111-1111-111111111111",
    )


def _config_get(
    tracking_uri=_TRACKING_URI,
    experiment_name="custom-experiment",
):
    def get(key):
        if key == "MLFLOW_TRACKING_URI":
            return tracking_uri
        if key == "MLFLOW_EXPERIMENT_NAME":
            return experiment_name
        return None

    return get


def _start_run_mock(run_id: str = _RUN_ID):
    run = MagicMock()
    run.info.run_id = run_id
    context = MagicMock()
    context.__enter__.return_value = run
    context.__exit__.return_value = False
    return context, run


@pytest.mark.parametrize("bad_uri", [None, "", 0, False])
def test_log_finished_run_raises_when_tracking_uri_missing_or_invalid(bad_uri):
    artifact = _artifact()
    with (
        patch(_CONFIG, side_effect=_config_get(tracking_uri=bad_uri)),
        pytest.raises(EnvironmentError, match="misconfigured MLFLOW_TRACKING_URI"),
    ):
        MlflowTrackingServices.log_finished_run(artifact, [])


def test_log_finished_run_defaults_experiment_when_name_missing():
    artifact = _artifact()
    start_run, _run = _start_run_mock()

    def get(key):
        if key == "MLFLOW_TRACKING_URI":
            return _TRACKING_URI
        if key == "MLFLOW_EXPERIMENT_NAME":
            return None
        return None

    with patch(_MLFLOW) as mlflow_mock:
        mlflow_mock.start_run.return_value = start_run
        with patch(_CONFIG, side_effect=get):
            MlflowTrackingServices.log_finished_run(artifact, [])

    mlflow_mock.set_experiment.assert_called_once_with("fiery-spirit")


def test_log_finished_run_uses_configured_experiment_name():
    artifact = _artifact()
    start_run, _run = _start_run_mock()

    with patch(_MLFLOW) as mlflow_mock:
        mlflow_mock.start_run.return_value = start_run
        with patch(_CONFIG, side_effect=_config_get(experiment_name="my-experiment")):
            MlflowTrackingServices.log_finished_run(artifact, [])

    mlflow_mock.set_experiment.assert_called_once_with("my-experiment")


def test_log_finished_run_registers_model_and_returns_run_id():
    artifact = _artifact(hf_repo_id="org/Fiery-Screener")
    metric = _metric()
    start_run, run = _start_run_mock()

    with patch(_MLFLOW) as mlflow_mock:
        mlflow_mock.start_run.return_value = start_run
        with patch(_CONFIG, side_effect=_config_get()):
            run_id = MlflowTrackingServices.log_finished_run(artifact, [metric])

    assert run_id == _RUN_ID
    mlflow_mock.set_tracking_uri.assert_called_once_with(_TRACKING_URI)
    mlflow_mock.start_run.assert_called_once_with(run_name=artifact.session_id)
    mlflow_mock.log_params.assert_called_once_with(
        {
            "tier": ModelTier.CLOUD.value,
            "role": ModelRole.SCREENER.value,
            "stage": TrainingStage.LORA.value,
            "architecture": "vit-small",
            "precision": TrainingPrecision.FP32.value,
            "session_id": artifact.session_id,
            "param_count": artifact.param_count,
        }
    )
    mlflow_mock.log_metric.assert_called_once_with(
        f"{metric.split}_{metric.name}",
        0.91,
    )
    mlflow_mock.set_tags.assert_called_once_with(
        {
            "storage_path": artifact.storage_path,
            "signature": artifact.signature,
            "hf_repo_id": "org/Fiery-Screener",
            "hf_revision": "",
            "parent_id": "",
        }
    )
    mlflow_mock.log_dict.assert_called_once_with(
        {
            "storage_path": artifact.storage_path,
            "signature": artifact.signature,
            "session_id": artifact.session_id,
        },
        "artifact.json",
    )
    mlflow_mock.register_model.assert_called_once_with(
        model_uri=f"runs:/{_RUN_ID}/artifact.json",
        name="Fiery-Screener",
    )


def test_log_finished_run_uses_mlflow_utils_hf_repo_id_when_artifact_missing():
    artifact = _artifact(hf_repo_id=None)
    start_run, _run = _start_run_mock()

    with (
        patch(_MLFLOW) as mlflow_mock,
        patch(_MLFLOW_UTILS) as utils_mock,
    ):
        mlflow_mock.start_run.return_value = start_run
        utils_mock.hf_repo_id.return_value = "namespace/Fiery-Screener"
        with patch(_CONFIG, side_effect=_config_get()):
            MlflowTrackingServices.log_finished_run(artifact, [])

    utils_mock.hf_repo_id.assert_called_once_with(ModelTier.CLOUD, ModelRole.SCREENER)
    tags = mlflow_mock.set_tags.call_args.args[0]
    assert tags["hf_repo_id"] == "namespace/Fiery-Screener"


def test_log_finished_run_skips_mlflow_utils_when_artifact_has_hf_repo_id():
    artifact = _artifact(hf_repo_id="preset/repo")
    start_run, _run = _start_run_mock()

    with (
        patch(_MLFLOW) as mlflow_mock,
        patch(_MLFLOW_UTILS) as utils_mock,
    ):
        mlflow_mock.start_run.return_value = start_run
        with patch(_CONFIG, side_effect=_config_get()):
            MlflowTrackingServices.log_finished_run(artifact, [])

    utils_mock.hf_repo_id.assert_not_called()


@pytest.mark.parametrize("bad_uri", [None, "", 123])
def test_alias_production_raises_when_tracking_uri_missing_or_invalid(bad_uri):
    with (
        patch(_CONFIG, side_effect=_config_get(tracking_uri=bad_uri)),
        pytest.raises(EnvironmentError, match="misconfigured MLFLOW_TRACKING_URI"),
    ):
        MlflowTrackingServices.alias_production("Fiery-Screener")


def test_alias_production_raises_when_no_registered_versions():
    client = MagicMock()
    client.search_model_versions.return_value = []

    with patch(_MLFLOW) as mlflow_mock:
        mlflow_mock.MlflowClient.return_value = client
        with patch(_CONFIG, side_effect=_config_get()):
            with pytest.raises(
                RuntimeError, match="no registered versions for Fiery-Screener"
            ):
                MlflowTrackingServices.alias_production("Fiery-Screener")

    client.search_model_versions.assert_called_once_with("name='Fiery-Screener'")
    client.set_registered_model_alias.assert_not_called()


def test_alias_production_aliases_max_version_when_version_omitted():
    client = MagicMock()
    client.search_model_versions.return_value = [
        MagicMock(version="1"),
        MagicMock(version="7"),
        MagicMock(version="3"),
    ]

    with patch(_MLFLOW) as mlflow_mock:
        mlflow_mock.MlflowClient.return_value = client
        with patch(_CONFIG, side_effect=_config_get()):
            MlflowTrackingServices.alias_production("Fiery-Screener")

    mlflow_mock.set_tracking_uri.assert_called_once_with(_TRACKING_URI)
    client.set_registered_model_alias.assert_called_once_with(
        "Fiery-Screener", "production", "7"
    )


def test_alias_production_skips_search_when_version_provided():
    client = MagicMock()

    with patch(_MLFLOW) as mlflow_mock:
        mlflow_mock.MlflowClient.return_value = client
        with patch(_CONFIG, side_effect=_config_get()):
            MlflowTrackingServices.alias_production("Fiery-Screener", version="4")

    client.search_model_versions.assert_not_called()
    client.set_registered_model_alias.assert_called_once_with(
        "Fiery-Screener", "production", "4"
    )


@pytest.mark.parametrize("bad_uri", [None, "", 123])
def test_registered_version_for_run_raises_when_tracking_uri_missing_or_invalid(
    bad_uri,
):
    with (
        patch(_CONFIG, side_effect=_config_get(tracking_uri=bad_uri)),
        pytest.raises(EnvironmentError, match="misconfigured MLFLOW_TRACKING_URI"),
    ):
        MlflowTrackingServices.registered_version_for_run("Fiery-Screener", _RUN_ID)


def test_registered_version_for_run_raises_when_no_matching_version():
    client = MagicMock()
    client.search_model_versions.return_value = []

    with patch(_MLFLOW) as mlflow_mock:
        mlflow_mock.MlflowClient.return_value = client
        with patch(_CONFIG, side_effect=_config_get()):
            with pytest.raises(
                RuntimeError,
                match=f"no registered version for Fiery-Screener run_id={_RUN_ID}",
            ):
                MlflowTrackingServices.registered_version_for_run(
                    "Fiery-Screener", _RUN_ID
                )

    client.search_model_versions.assert_called_once_with(
        filter_string=f"name = 'Fiery-Screener' AND run_id = '{_RUN_ID}'"
    )


def test_registered_version_for_run_returns_single_version():
    client = MagicMock()
    client.search_model_versions.return_value = [MagicMock(version="12")]

    with patch(_MLFLOW) as mlflow_mock:
        mlflow_mock.MlflowClient.return_value = client
        with patch(_CONFIG, side_effect=_config_get()):
            version = MlflowTrackingServices.registered_version_for_run(
                "Fiery-Screener", _RUN_ID
            )

    assert version == "12"
    mlflow_mock.set_tracking_uri.assert_called_once_with(_TRACKING_URI)


def test_registered_version_for_run_picks_max_when_multiple_versions_share_run():
    client = MagicMock()
    client.search_model_versions.return_value = [
        MagicMock(version="3"),
        MagicMock(version="9"),
        MagicMock(version="5"),
    ]

    with patch(_MLFLOW) as mlflow_mock:
        mlflow_mock.MlflowClient.return_value = client
        with patch(_CONFIG, side_effect=_config_get()):
            version = MlflowTrackingServices.registered_version_for_run(
                "Fiery-Screener", _RUN_ID
            )

    assert version == "9"
