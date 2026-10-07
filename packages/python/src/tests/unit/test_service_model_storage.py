"""
Author: Sean Froning
Created Date: 8.20.2026
Unit tests for ModelStorageServices s3 client
"""

import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

import pytest
import torch
from safetensors.torch import load, save
from fiery_python import models_s3
from fiery_python import MODEL_BUCKET_NAME, ModelStorageServices

HMAC_META_KEY = "artifact-hmac-sha256"
_WEIGHTS_KEY = "cloud/screener/art-1.safetensors"
_SIDECAR_KEY = "cloud/screener/art-1.json"


@pytest.fixture(autouse=True)
def _reset_s3_client():
    models_s3.reset()
    yield
    models_s3.reset()


def test_artifact_hmac_secret_requires_env(monkeypatch):
    monkeypatch.delenv("MODELS_ARTIFACT_HMAC_KEY", raising=False)

    with pytest.raises(RuntimeError, match="MODELS_ARTIFACT_HMAC_KEY"):
        ModelStorageServices._artifact_hmac_secret()


def test_get_client_requires_credentials(monkeypatch):
    monkeypatch.delenv("MODELS_BUCKET_KEY_ID", raising=False)
    monkeypatch.delenv("MODELS_BUCKET_KEY_SECRET", raising=False)

    with pytest.raises(RuntimeError, match="credentials"):
        models_s3.get_client()


def test_get_client_reuses_singleton(monkeypatch):
    monkeypatch.setenv("MODELS_BUCKET_KEY_ID", "id")
    monkeypatch.setenv("MODELS_BUCKET_KEY_SECRET", "secret")
    monkeypatch.setenv("S3_BUCKET_URL", "https://s3.example")
    fake = MagicMock()

    with patch(
        "fiery_python.core.storage.boto3.client", return_value=fake
    ) as boto_client:
        first = models_s3.get_client()
        second = models_s3.get_client()

    assert first is fake
    assert second is fake
    boto_client.assert_called_once()


def test_sidecar_key_swaps_suffix():
    assert ModelStorageServices.sidecar_key(_WEIGHTS_KEY) == _SIDECAR_KEY


def test_sidecar_key_rejects_non_safetensors():
    with pytest.raises(ValueError, match="safetensors"):
        ModelStorageServices.sidecar_key("cloud/screener/art-1.pkl")


def test_save_artifact_uploads_weights_and_sidecar(monkeypatch):
    monkeypatch.setenv("MODELS_ARTIFACT_HMAC_KEY", "unit-secret")
    state_dict = {"weight": torch.ones(2)}
    sidecar = {"architecture": "vit_small_patch16_224"}

    with patch.object(models_s3, "put_bytes") as put_bytes:
        result = ModelStorageServices.save_artifact(state_dict, sidecar, _WEIGHTS_KEY)

    assert result == _WEIGHTS_KEY
    assert put_bytes.call_count == 2
    weights_args, weights_kwargs = put_bytes.call_args_list[0]
    sidecar_args, sidecar_kwargs = put_bytes.call_args_list[1]
    assert weights_args[0] == MODEL_BUCKET_NAME
    assert weights_args[1] == _WEIGHTS_KEY
    weights_body = weights_args[2]
    expected_weights = hmac.new(
        b"unit-secret", weights_body, hashlib.sha256
    ).hexdigest()
    assert weights_kwargs["metadata"][HMAC_META_KEY] == expected_weights
    assert sidecar_args[1] == _SIDECAR_KEY
    sidecar_payload = json.loads(sidecar_args[2].decode("utf-8"))
    assert sidecar_payload["architecture"] == "vit_small_patch16_224"
    assert sidecar_payload["weights_hmac"] == expected_weights
    sidecar_expected = hmac.new(
        b"unit-secret", sidecar_args[2], hashlib.sha256
    ).hexdigest()
    assert sidecar_kwargs["metadata"][HMAC_META_KEY] == sidecar_expected
    assert sidecar_kwargs["content_type"] == "application/json"


def test_load_artifact_deserializes_after_hmac_check(monkeypatch):
    monkeypatch.setenv("MODELS_ARTIFACT_HMAC_KEY", "unit-secret")
    state_dict = {"weight": torch.ones(2)}
    weights = save(state_dict)
    weights_sig = hmac.new(b"unit-secret", weights, hashlib.sha256).hexdigest()
    sidecar_body = json.dumps(
        {"architecture": "vit_small_patch16_224", "weights_hmac": weights_sig},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    sidecar_sig = hmac.new(b"unit-secret", sidecar_body, hashlib.sha256).hexdigest()

    def fake_get_object(_bucket, key):
        if key == _WEIGHTS_KEY:
            return {
                "Body": _Bytes(weights),
                "Metadata": {HMAC_META_KEY: weights_sig},
            }
        return {
            "Body": _Bytes(sidecar_body),
            "Metadata": {HMAC_META_KEY: sidecar_sig},
        }

    with (
        patch.object(models_s3, "get_object", side_effect=fake_get_object),
        patch.object(
            models_s3,
            "head_object",
            return_value={"Metadata": {HMAC_META_KEY: weights_sig}},
        ),
    ):
        loaded_state, loaded_sidecar = ModelStorageServices.load_artifact(
            _WEIGHTS_KEY,
            is_weights=True,
        )

    torch.testing.assert_close(loaded_state["weight"], state_dict["weight"])
    assert loaded_sidecar["architecture"] == "vit_small_patch16_224"
    assert loaded_sidecar["weights_hmac"] == weights_sig
    restored = load(weights)
    torch.testing.assert_close(restored["weight"], state_dict["weight"])


def test_load_artifact_refuses_missing_hmac_metadata(monkeypatch):
    monkeypatch.setenv("MODELS_ARTIFACT_HMAC_KEY", "unit-secret")
    obj = {
        "Body": _Bytes(b"weights"),
        "Metadata": {},
    }

    with patch.object(models_s3, "get_object", return_value=obj):
        with pytest.raises(RuntimeError, match="missing artifact-hmac-sha256"):
            ModelStorageServices.load_artifact(_WEIGHTS_KEY, is_weights=True)


def test_load_artifact_refuses_hmac_mismatch(monkeypatch):
    monkeypatch.setenv("MODELS_ARTIFACT_HMAC_KEY", "unit-secret")
    obj = {
        "Body": _Bytes(b"weights"),
        "Metadata": {HMAC_META_KEY: "0" * 64},
    }

    with patch.object(models_s3, "get_object", return_value=obj):
        with pytest.raises(RuntimeError, match="HMAC verification failed"):
            ModelStorageServices.load_artifact(_WEIGHTS_KEY, is_weights=True)


def test_head_hmac_returns_metadata_digest():
    obj = {"Metadata": {HMAC_META_KEY: "a" * 64}}
    with patch.object(models_s3, "head_object", return_value=obj) as head_object:
        digest = ModelStorageServices.head_hmac(_WEIGHTS_KEY)
    assert digest == "a" * 64
    head_object.assert_called_once_with(MODEL_BUCKET_NAME, _WEIGHTS_KEY)


def test_head_hmac_refuses_missing_metadata():
    with patch.object(models_s3, "head_object", return_value={"Metadata": {}}):
        with pytest.raises(RuntimeError, match="missing artifact-hmac-sha256"):
            ModelStorageServices.head_hmac(_WEIGHTS_KEY)


class _Bytes:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def close(self) -> None:
        return None
