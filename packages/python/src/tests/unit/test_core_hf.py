"""
Author: Sean Froning
Created Date: 10.7.2026
Unit tests for the process-local Hugging Face client
"""

from unittest.mock import MagicMock, patch

import pytest
from my_python import hf


@pytest.fixture(autouse=True)
def _reset_hf_client():
    hf.reset()
    yield
    hf.reset()


def test_get_client_requires_token(monkeypatch):
    monkeypatch.delenv("HF_TOKEN", raising=False)

    with pytest.raises(EnvironmentError, match="HF_TOKEN"):
        hf.get_client()


def test_get_client_passes_token(monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "hf_test")
    client = MagicMock()

    with patch("my_python.core.hf.HfApi", return_value=client) as ctor:
        assert hf.get_client() is client
        assert hf.get_client() is client

    ctor.assert_called_once_with(token="hf_test")


def test_repo_id_prefixes_namespace(monkeypatch):
    monkeypatch.setenv("HF_MODEL_NAMESPACE", "org")
    assert hf.repo_id("screen") == "org/screen"


def test_repo_id_without_namespace(monkeypatch):
    monkeypatch.delenv("HF_MODEL_NAMESPACE", raising=False)
    assert hf.namespace() is None
    assert hf.repo_id("screen") == "screen"
