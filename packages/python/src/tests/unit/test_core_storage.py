"""
Author: Sean Froning
Created Date: 8.20.2026
Unit tests for process-local S3 clients
"""

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from fiery_python import models_s3, r2_s3


@pytest.fixture(autouse=True)
def _reset_s3_clients():
    models_s3.reset()
    r2_s3.reset()
    yield
    models_s3.reset()
    r2_s3.reset()


def test_r2_get_client_requires_credentials(monkeypatch):
    monkeypatch.delenv("R2_BUCKET_KEY_ID", raising=False)
    monkeypatch.delenv("R2_BUCKET_KEY_SECRET", raising=False)

    with pytest.raises(RuntimeError, match="R2 credentials"):
        r2_s3.get_client()


def test_put_bytes_requires_key_and_body():
    with pytest.raises(ValueError, match="key and body"):
        models_s3.put_bytes("models", "", b"x")
    with pytest.raises(ValueError, match="key and body"):
        models_s3.put_bytes("models", "key.pkl", b"")


def test_put_bytes_forwards_metadata():
    client = MagicMock()
    with patch.object(models_s3, "get_client", return_value=client):
        models_s3.put_bytes(
            "models",
            "art.pkl",
            b"body",
            content_type="application/octet-stream",
            metadata={"artifact-hmac-sha256": "abc"},
        )

    client.put_object.assert_called_once_with(
        Bucket="models",
        Key="art.pkl",
        Body=b"body",
        ContentType="application/octet-stream",
        Metadata={"artifact-hmac-sha256": "abc"},
    )


def test_head_object_returns_metadata():
    client = MagicMock()
    client.head_object.return_value = {
        "Metadata": {"artifact-hmac-sha256": "abc"},
    }
    with patch.object(models_s3, "get_client", return_value=client):
        obj = models_s3.head_object("models", "art.pkl")
    client.head_object.assert_called_once_with(Bucket="models", Key="art.pkl")
    assert obj["Metadata"]["artifact-hmac-sha256"] == "abc"


def test_exists_false_on_missing_object():
    client = MagicMock()
    client.head_object.side_effect = ClientError(
        {"Error": {"Code": "404", "Message": "Not Found"}},
        "HeadObject",
    )
    with patch.object(models_s3, "get_client", return_value=client):
        assert models_s3.exists("models", "missing.pkl") is False


def test_get_bytes_reads_body():
    client = MagicMock()
    client.get_object.return_value = {"Body": MagicMock(read=lambda: b"npz")}
    with patch.object(r2_s3, "get_client", return_value=client):
        assert r2_s3.get_bytes("unrefined", "hephaestus/abc.npz") == b"npz"
