"""
Author: Sean Froning
Created Date: 9.21.2026
Unit tests for trainer checkpoint save
"""

from unittest.mock import patch

import pytest
from fiery_python import ModelRole, ModelTier
from src.save_checkpoint import save_checkpoint

_STORAGE_PATH = "cloud/screener/sess-1.safetensors"
_WEIGHTS = b"checkpoint-bytes"
_HF_REPO_ID = "fiery/cloud-screener"


def _spec(**overrides) -> dict:
    data = {
        "session_id": "sess-1",
        "tier": ModelTier.CLOUD.value,
        "role": ModelRole.SCREENER.value,
    }
    data.update(overrides)
    return data


def _sidecar(**overrides) -> dict:
    data = {"session_id": "sess-1"}
    data.update(overrides)
    return data


@pytest.mark.parametrize("weights_bytes", [None, b""])
def test_save_checkpoint_skips_when_weights_missing(weights_bytes):
    sidecar = _sidecar()
    with (
        patch("fiery_python.MlflowUtils.hf_repo_id") as hf_repo_id,
        patch("fiery_python.HubCheckpointServices.push_commit") as push,
    ):
        result = save_checkpoint(
            _spec(),
            storage_path=_STORAGE_PATH,
            weights_bytes=weights_bytes,
            sidecar=sidecar,
        )
    assert result is sidecar
    assert "hf_repo_id" not in result
    hf_repo_id.assert_not_called()
    push.assert_not_called()


def test_save_checkpoint_returns_sidecar_when_spec_malformed():
    sidecar = _sidecar()
    with patch("fiery_python.HubCheckpointServices.push_commit") as push:
        result = save_checkpoint(
            _spec(tier="not-a-valid-tier"),
            storage_path=_STORAGE_PATH,
            weights_bytes=_WEIGHTS,
            sidecar=sidecar,
        )
    assert result is sidecar
    assert "hf_repo_id" not in result
    push.assert_not_called()


def test_save_checkpoint_success_writes_hf_fields():
    sidecar = _sidecar()
    with (
        patch(
            "fiery_python.MlflowUtils.hf_repo_id",
            return_value=_HF_REPO_ID,
        ) as hf_repo_id,
        patch(
            "fiery_python.HubCheckpointServices.push_commit",
            return_value="rev-abc",
        ) as push,
    ):
        result = save_checkpoint(
            _spec(),
            storage_path=_STORAGE_PATH,
            weights_bytes=_WEIGHTS,
            sidecar=sidecar,
        )
    hf_repo_id.assert_called_once_with(ModelTier.CLOUD, ModelRole.SCREENER)
    push.assert_called_once_with(
        _STORAGE_PATH,
        _WEIGHTS,
        sidecar,
        repo_id=_HF_REPO_ID,
    )
    assert result is sidecar
    assert result["hf_repo_id"] == _HF_REPO_ID
    assert result["hf_revision"] == "rev-abc"


def test_save_checkpoint_retries_then_succeeds():
    sidecar = _sidecar()
    with (
        patch("fiery_python.MlflowUtils.hf_repo_id", return_value=_HF_REPO_ID),
        patch(
            "fiery_python.HubCheckpointServices.push_commit",
            side_effect=[
                RuntimeError("hub down"),
                RuntimeError("hub down"),
                "rev-ok",
            ],
        ) as push,
        patch("src.save_checkpoint.time.sleep") as sleep,
    ):
        result = save_checkpoint(
            _spec(),
            storage_path=_STORAGE_PATH,
            weights_bytes=_WEIGHTS,
            sidecar=sidecar,
        )
    assert push.call_count == 3
    assert sleep.call_count == 2
    assert result["hf_repo_id"] == _HF_REPO_ID
    assert result["hf_revision"] == "rev-ok"


def test_save_checkpoint_returns_sidecar_without_hf_keys_when_all_retries_fail():
    sidecar = _sidecar()
    with (
        patch("fiery_python.MlflowUtils.hf_repo_id", return_value=_HF_REPO_ID),
        patch(
            "fiery_python.HubCheckpointServices.push_commit",
            side_effect=RuntimeError("hub down"),
        ) as push,
        patch("src.save_checkpoint.time.sleep") as sleep,
    ):
        result = save_checkpoint(
            _spec(),
            storage_path=_STORAGE_PATH,
            weights_bytes=_WEIGHTS,
            sidecar=sidecar,
        )
    assert push.call_count == 3
    assert sleep.call_count == 3
    assert result is sidecar
    assert "hf_repo_id" not in result
    assert "hf_revision" not in result
