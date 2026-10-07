"""
Author: Sean Froning
Created Date: 9.21.2026
Unit tests for MlflowUtils
"""

import pytest
from fiery_python.enums import ModelRole, ModelTier
from fiery_python.utils.mlflow import MlflowUtils


def _patch_namespace(monkeypatch, value):
    monkeypatch.setattr(
        "fiery_python.utils.mlflow.config.get",
        lambda key: value if key == "HF_MODEL_NAMESPACE" else None,
    )


@pytest.mark.parametrize(
    "tier,role,model_name",
    [
        (ModelTier.CLOUD, ModelRole.SCREENER, "Fiery-Screener"),
        (ModelTier.CLOUD, ModelRole.TEACHER, "Fiery-Teacher"),
        (ModelTier.EDGE, ModelRole.STUDENT, "Fiery-Student"),
    ],
)
def test_hf_repo_id_returns_namespace_and_registered_name(
    monkeypatch, tier, role, model_name
):
    _patch_namespace(monkeypatch, "sfroning88")
    assert MlflowUtils.hf_repo_id(tier, role) == f"sfroning88/{model_name}"


def test_hf_repo_id_raises_when_namespace_missing(monkeypatch):
    monkeypatch.setattr(
        "fiery_python.utils.mlflow.config.get",
        lambda key: None,
    )
    with pytest.raises(EnvironmentError, match="HF_MODEL_NAMESPACE"):
        MlflowUtils.hf_repo_id(ModelTier.CLOUD, ModelRole.SCREENER)


@pytest.mark.parametrize("bad_namespace", ["", 5])
def test_hf_repo_id_raises_when_namespace_empty_or_not_str(monkeypatch, bad_namespace):
    _patch_namespace(monkeypatch, bad_namespace)
    with pytest.raises(EnvironmentError, match="HF_MODEL_NAMESPACE"):
        MlflowUtils.hf_repo_id(ModelTier.CLOUD, ModelRole.SCREENER)


def test_hf_repo_id_raises_key_error_for_unknown_tier_role(monkeypatch):
    _patch_namespace(monkeypatch, "sfroning88")
    with pytest.raises(KeyError):
        MlflowUtils.hf_repo_id(ModelTier.EDGE, ModelRole.SCREENER)
