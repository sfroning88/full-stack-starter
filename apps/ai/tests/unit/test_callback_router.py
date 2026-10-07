"""
Author: Sean Froning
Created Date: 9.21.2026
Unit tests for callback train router
"""

import asyncio
from decimal import Decimal
from unittest.mock import patch

from starlette.requests import Request
from fiery_python import (
    ModelRole,
    ModelTier,
    TrainingPrecision,
    TrainingSession,
    TrainingSignal,
    TrainingStage,
    TrainingStatus,
)
from integrations.callback.router import callback_train
from integrations.callback.schemas import CallbackRequest


def _payload() -> CallbackRequest:
    return CallbackRequest(
        session_id="11111111-1111-1111-1111-111111111111",
        tier=ModelTier.CLOUD,
        role=ModelRole.SCREENER,
        precision=TrainingPrecision.FP32,
        storage_path="cloud/screener/art-1.safetensors",
        signature="b" * 64,
        param_count=22000000,
        architecture="vit-small",
        sparsity=Decimal("0"),
        metrics=[],
        nonce="nonce-1",
        threshold=Decimal("0.5"),
        abstention_band=Decimal("0"),
        transform_hash="a" * 64,
        op_version=1,
    )


def _session() -> TrainingSession:
    return TrainingSession(
        id="11111111-1111-1111-1111-111111111111",
        signal=TrainingSignal.DEFORMATION,
        stage=TrainingStage.LORA,
        status=TrainingStatus.EXECUTING,
        samples=10,
        seed=42,
        hyperparameter_lora_id="lora-1",
        contract_id="contract-1",
        version_id="ver-1",
    )


def _request() -> Request:
    return Request({"type": "http", "method": "POST", "path": "/", "headers": []})


def test_callback_train_persists_when_mlflow_logging_fails():
    payload = _payload()
    session = _session()
    request = _request()

    with (
        patch(
            "integrations.callback.router.CallbackVerifyArtifact.verify_body_signature"
        ),
        patch(
            "integrations.callback.router.CallbackVerifyArtifact.verify_object_metadata"
        ),
        patch(
            "integrations.callback.router.TrainPersistService.select_session",
            return_value=session,
        ),
        patch(
            "integrations.callback.router.MlflowTrackingServices.log_finished_run",
            side_effect=RuntimeError("mlflow down"),
        ),
        patch(
            "integrations.callback.router.CallbackPersistService.upsert_artifact"
        ) as upsert_artifact,
        patch(
            "integrations.callback.router.CallbackPersistService.upsert_metrics"
        ) as upsert_metrics,
        patch(
            "integrations.callback.router.TrainPersistService.upsert_session"
        ) as upsert_session,
    ):
        response = asyncio.run(
            callback_train(request, payload, x_callback_hmac="digest")
        )

    assert response.session_id == session.id
    upsert_artifact.assert_called_once()
    saved = upsert_artifact.call_args.args[0]
    assert saved.mlflow_run_id is None
    upsert_metrics.assert_called_once()
    upsert_session.assert_called_once()
    assert session.status is TrainingStatus.COMPLETED
    assert session.finished_at is not None


def test_callback_train_sets_mlflow_run_id_when_logging_succeeds():
    payload = _payload()
    session = _session()
    request = _request()

    with (
        patch(
            "integrations.callback.router.CallbackVerifyArtifact.verify_body_signature"
        ),
        patch(
            "integrations.callback.router.CallbackVerifyArtifact.verify_object_metadata"
        ),
        patch(
            "integrations.callback.router.TrainPersistService.select_session",
            return_value=session,
        ),
        patch(
            "integrations.callback.router.MlflowTrackingServices.log_finished_run",
            return_value="run-abc",
        ),
        patch(
            "integrations.callback.router.CallbackPersistService.upsert_artifact"
        ) as upsert_artifact,
        patch("integrations.callback.router.CallbackPersistService.upsert_metrics"),
        patch("integrations.callback.router.TrainPersistService.upsert_session"),
    ):
        asyncio.run(callback_train(request, payload, x_callback_hmac="digest"))

    saved = upsert_artifact.call_args.args[0]
    assert saved.mlflow_run_id == "run-abc"
