"""
Author: Sean Froning
Created Date: 9.21.2026
Unit tests for HubCheckpointServices
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from fiery_python.services.hub_checkpoint import HubCheckpointServices

_WEIGHTS_KEY = "cloud/screener/sess-1.safetensors"
_SIDECAR_KEY = "cloud/screener/sess-1.json"
_REPO_ID = "org/model-repo"
_HF_TOKEN = "hf_test_token"
_SIDECAR = {"spec": {"session_id": "sess-1"}, "architecture": "cnn"}
_WEIGHTS_BYTES = b"weights-bytes"


def test_push_commit_missing_token_raises_environment_error():
    with patch("fiery_python.services.hub_checkpoint.HF_TOKEN", None):
        with pytest.raises(EnvironmentError, match="misconfigured HF_TOKEN"):
            HubCheckpointServices.push_commit(
                _WEIGHTS_KEY,
                _WEIGHTS_BYTES,
                _SIDECAR,
                repo_id=_REPO_ID,
            )


def test_push_commit_malformed_session_id_raises_runtime_error():
    sidecar = {"spec": {"session_id": 1}, "architecture": "cnn"}
    with patch("fiery_python.services.hub_checkpoint.HF_TOKEN", _HF_TOKEN):
        with pytest.raises(RuntimeError, match="malformed session_id"):
            HubCheckpointServices.push_commit(
                _WEIGHTS_KEY,
                _WEIGHTS_BYTES,
                sidecar,
                repo_id=_REPO_ID,
            )


def test_push_commit_success_creates_repo_and_commit():
    fake_commit = MagicMock()
    fake_commit.oid = "commit-oid-abc"
    fake_api = MagicMock()
    fake_api.create_commit.return_value = fake_commit

    with (
        patch("fiery_python.services.hub_checkpoint.HF_TOKEN", _HF_TOKEN),
        patch(
            "fiery_python.services.hub_checkpoint.HfApi",
            return_value=fake_api,
        ) as hf_api_cls,
    ):
        oid = HubCheckpointServices.push_commit(
            _WEIGHTS_KEY,
            _WEIGHTS_BYTES,
            _SIDECAR,
            repo_id=_REPO_ID,
        )

    assert oid == "commit-oid-abc"
    hf_api_cls.assert_called_once_with(token=_HF_TOKEN)
    fake_api.create_repo.assert_called_once_with(
        repo_id=_REPO_ID,
        repo_type="model",
        private=True,
        exist_ok=True,
    )
    fake_api.create_commit.assert_called_once()
    commit_kwargs = fake_api.create_commit.call_args.kwargs
    assert commit_kwargs["repo_id"] == _REPO_ID
    assert commit_kwargs["repo_type"] == "model"
    operations = commit_kwargs["operations"]
    assert len(operations) == 2
    assert operations[0].path_in_repo == _WEIGHTS_KEY
    assert operations[0].path_or_fileobj.read() == _WEIGHTS_BYTES
    assert operations[1].path_in_repo == _SIDECAR_KEY
    sidecar_payload = json.loads(operations[1].path_or_fileobj.read().decode("utf-8"))
    assert sidecar_payload == _SIDECAR


def test_push_commit_rejects_non_safetensors_weights_key():
    with patch("fiery_python.services.hub_checkpoint.HF_TOKEN", _HF_TOKEN):
        with pytest.raises(ValueError, match="safetensors"):
            HubCheckpointServices.push_commit(
                "cloud/screener/sess-1.pkl",
                _WEIGHTS_BYTES,
                _SIDECAR,
                repo_id=_REPO_ID,
            )
