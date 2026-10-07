"""
Author: Sean Froning
Created Date: 8.24.2026
Unit tests for CallbackVerifyArtifact
"""

import hashlib
import hmac
import json
from decimal import Decimal
from unittest.mock import patch

import pytest
from fiery_python import (
    ModelMetric,
    ModelMetricName,
    ModelRole,
    ModelTier,
    TrainingPrecision,
    TrainingSplit,
)
from fiery_python.fastapi.error import error as AppError
from integrations.callback.schemas import CallbackRequest
from integrations.callback.services.verify_artifact import CallbackVerifyArtifact


def _payload(**overrides) -> CallbackRequest:
    data = {
        "session_id": "11111111-1111-1111-1111-111111111111",
        "tier": ModelTier.CLOUD,
        "role": ModelRole.SCREENER,
        "precision": TrainingPrecision.FP32,
        "storage_path": "cloud/screener/art-1.safetensors",
        "signature": "b" * 64,
        "param_count": 22000000,
        "architecture": "vit_small_patch16_224.augreg_in21k_ft_in1k",
        "sparsity": Decimal("0"),
        "metrics": [
            ModelMetric(
                name=ModelMetricName.RECALL,
                split=TrainingSplit.TEST,
                value=Decimal("0.910"),
                artifact_id="art-1",
            )
        ],
        "nonce": "nonce-1",
        "threshold": Decimal("0.5"),
        "abstention_band": Decimal("0.00000"),
        "transform_hash": "a" * 64,
        "op_version": 1,
    }
    data.update(overrides)
    return CallbackRequest(**data)


def _body_hmac(payload: CallbackRequest, secret: bytes) -> str:
    canonical = json.dumps(
        {
            "architecture": payload.architecture,
            "abstention_band": str(payload.abstention_band),
            "base_model_id": payload.base_model_id or "",
            "nonce": payload.nonce or "",
            "op_version": payload.op_version,
            "param_count": payload.param_count,
            "parent_id": payload.parent_id or "",
            "precision": payload.precision.value,
            "revision": payload.revision or "",
            "role": payload.role.value,
            "session_id": payload.session_id,
            "signature": payload.signature,
            "sparsity": str(payload.sparsity),
            "storage_path": payload.storage_path,
            "threshold": str(payload.threshold),
            "tier": payload.tier.value,
            "transform_hash": payload.transform_hash,
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return hmac.new(secret, canonical.encode("utf-8"), hashlib.sha256).hexdigest()


def test_verify_body_signature_accepts_matching_hmac():
    payload = _payload()
    secret = b"unit-secret"
    digest = _body_hmac(payload, secret)
    with patch(
        "integrations.callback.services.verify_artifact.ModelStorageServices._artifact_hmac_secret",
        return_value=secret,
    ):
        CallbackVerifyArtifact.verify_body_signature(payload, digest)


def test_verify_body_signature_raises_when_secret_missing():
    with patch(
        "integrations.callback.services.verify_artifact.ModelStorageServices._artifact_hmac_secret",
        side_effect=RuntimeError("MODELS_ARTIFACT_HMAC_KEY is not configured"),
    ):
        with pytest.raises(AppError, match="MODELS_ARTIFACT_HMAC_KEY"):
            CallbackVerifyArtifact.verify_body_signature(_payload(), "abc")


def test_verify_body_signature_raises_when_header_missing():
    with patch(
        "integrations.callback.services.verify_artifact.ModelStorageServices._artifact_hmac_secret",
        return_value=b"unit-secret",
    ):
        with pytest.raises(AppError, match="Callback HMAC missing") as err:
            CallbackVerifyArtifact.verify_body_signature(_payload(), "")
    assert err.value.status_code == 403


def test_verify_body_signature_raises_when_hmac_invalid():
    with patch(
        "integrations.callback.services.verify_artifact.ModelStorageServices._artifact_hmac_secret",
        return_value=b"unit-secret",
    ):
        with pytest.raises(AppError, match="Callback HMAC invalid") as err:
            CallbackVerifyArtifact.verify_body_signature(_payload(), "0" * 64)
    assert err.value.status_code == 403


def test_verify_object_metadata_accepts_matching_head():
    with patch(
        "integrations.callback.services.verify_artifact.ModelStorageServices.head_hmac",
        return_value="b" * 64,
    ) as head_hmac:
        CallbackVerifyArtifact.verify_object_metadata(
            "cloud/screener/art-1.safetensors", "b" * 64
        )
    head_hmac.assert_called_once_with("cloud/screener/art-1.safetensors")


def test_verify_object_metadata_raises_when_object_missing():
    with patch(
        "integrations.callback.services.verify_artifact.ModelStorageServices.head_hmac",
        side_effect=RuntimeError("missing"),
    ):
        with pytest.raises(AppError, match="Artifact object not found") as err:
            CallbackVerifyArtifact.verify_object_metadata(
                "cloud/screener/art-1.safetensors", "b" * 64
            )
    assert err.value.status_code == 403


def test_verify_object_metadata_raises_when_digest_mismatch():
    with patch(
        "integrations.callback.services.verify_artifact.ModelStorageServices.head_hmac",
        return_value="a" * 64,
    ):
        with pytest.raises(AppError, match="artifact-hmac-sha256") as err:
            CallbackVerifyArtifact.verify_object_metadata(
                "cloud/screener/art-1.safetensors", "b" * 64
            )
    assert err.value.status_code == 403
