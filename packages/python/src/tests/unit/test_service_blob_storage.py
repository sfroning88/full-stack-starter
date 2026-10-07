"""
Author: Sean Froning
Created Date: 8.20.2026
Unit tests for BlobStorageServices R2 dataset blobs
"""

import hashlib
from unittest.mock import patch

import pytest
from fiery_python import (
    STORAGE_SHARD_BUCKET_NAME,
    STORAGE_UNREFINED_BUCKET_NAME,
    BlobStorageServices,
    TrainingSampleSource,
    TrainingSplit,
    r2_s3,
)


@pytest.fixture(autouse=True)
def _reset_r2_client():
    r2_s3.reset()
    yield
    r2_s3.reset()


def test_unrefined_key_uses_source_value_and_digest():
    digest = "a" * 64
    key = BlobStorageServices._unrefined_key(TrainingSampleSource.HEPHAESTUS, digest)
    assert key == f"hephaestus/{digest}.npz"


def test_shard_and_manifest_keys():
    shard = BlobStorageServices._shard_key(
        "contract-1", "hash-1", TrainingSplit.TRAIN, 7
    )
    manifest = BlobStorageServices._manifest_key("contract-1", "hash-1")
    assert shard == "contract-1/hash-1/train-00007.tar"
    assert manifest == "contract-1/hash-1/manifest.json"


def test_put_unrefined_uploads_when_missing():
    body = b"npz-bytes"
    digest = hashlib.sha256(body).hexdigest()
    expected_key = f"hephaestus/{digest}.npz"

    with (
        patch.object(r2_s3, "exists", return_value=False) as exists,
        patch.object(r2_s3, "put_bytes") as put_bytes,
    ):
        key = BlobStorageServices.put_unrefined(TrainingSampleSource.HEPHAESTUS, body)

    assert key == expected_key
    exists.assert_called_once_with(STORAGE_UNREFINED_BUCKET_NAME, expected_key)
    put_bytes.assert_called_once_with(
        STORAGE_UNREFINED_BUCKET_NAME,
        expected_key,
        body,
        content_type="application/x-npz",
    )


def test_put_unrefined_skips_upload_when_present():
    body = b"npz-bytes"
    digest = hashlib.sha256(body).hexdigest()
    expected_key = f"okada/{digest}.npz"

    with (
        patch.object(r2_s3, "exists", return_value=True) as exists,
        patch.object(r2_s3, "put_bytes") as put_bytes,
    ):
        key = BlobStorageServices.put_unrefined(TrainingSampleSource.OKADA, body)

    assert key == expected_key
    exists.assert_called_once_with(STORAGE_UNREFINED_BUCKET_NAME, expected_key)
    put_bytes.assert_not_called()


def test_get_unrefined_reads_unrefined_bucket():
    with patch.object(r2_s3, "get_bytes", return_value=b"npz") as get_bytes:
        body = BlobStorageServices.get_unrefined("hephaestus/abc.npz")

    assert body == b"npz"
    get_bytes.assert_called_once_with(
        STORAGE_UNREFINED_BUCKET_NAME, "hephaestus/abc.npz"
    )


def test_put_shard_uploads_tar():
    body = b"tar-bytes"
    expected_key = "contract-1/hash-1/validate-00003.tar"

    with patch.object(r2_s3, "put_bytes") as put_bytes:
        key = BlobStorageServices.put_shard(
            "contract-1", "hash-1", TrainingSplit.VALIDATE, 3, body
        )

    assert key == expected_key
    put_bytes.assert_called_once_with(
        STORAGE_SHARD_BUCKET_NAME,
        expected_key,
        body,
        content_type="application/x-tar",
    )


def test_get_shard_reads_shard_bucket():
    with patch.object(r2_s3, "get_bytes", return_value=b"tar") as get_bytes:
        body = BlobStorageServices.get_shard("contract-1/hash-1/train-00000.tar")

    assert body == b"tar"
    get_bytes.assert_called_once_with(
        STORAGE_SHARD_BUCKET_NAME, "contract-1/hash-1/train-00000.tar"
    )


def test_put_manifest_uploads_json():
    body = b'{"shards": 1}'
    expected_key = "contract-1/hash-1/manifest.json"

    with patch.object(r2_s3, "put_bytes") as put_bytes:
        key = BlobStorageServices.put_manifest("contract-1", "hash-1", body)

    assert key == expected_key
    put_bytes.assert_called_once_with(
        STORAGE_SHARD_BUCKET_NAME,
        expected_key,
        body,
        content_type="application/json",
    )


def test_exists_delegates_to_r2():
    with patch.object(r2_s3, "exists", return_value=True) as exists:
        assert BlobStorageServices.exists("unrefined", "hephaestus/abc.npz") is True

    exists.assert_called_once_with("unrefined", "hephaestus/abc.npz")
