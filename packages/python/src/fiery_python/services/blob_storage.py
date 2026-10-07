"""
Author: Sean Froning
Created Date: 8.20.2026
S3-backed compressed numpy storage for dataset blobs
"""

import hashlib
from ..constants import STORAGE_UNREFINED_BUCKET_NAME, STORAGE_SHARD_BUCKET_NAME
from ..core import logging, r2_s3
from ..enums import TrainingSplit, TrainingSampleSource

logger = logging.get_logger(__name__)


class BlobStorageServices:
    """S3-backed joblib pickle storage shared across training (writer) and inference (reader)"""

    @staticmethod
    def _unrefined_key(source: TrainingSampleSource, sha256: str) -> str:
        return f"{source.value}/{sha256}.npz"

    @staticmethod
    def _shard_key(
        contract_id: str, transform_hash: str, split: TrainingSplit, index: int
    ) -> str:
        return f"{contract_id}/{transform_hash}/{split.value}-{index:05d}.tar"

    @staticmethod
    def _manifest_key(contract_id: str, transform_hash: str) -> str:
        return f"{contract_id}/{transform_hash}/manifest.json"

    @classmethod
    def put_unrefined(cls, source: TrainingSampleSource, body: bytes) -> str:
        """Hash body, skip upload if object already exists, return the key"""
        key = cls._unrefined_key(source, hashlib.sha256(body).hexdigest())
        if r2_s3.exists(STORAGE_UNREFINED_BUCKET_NAME, key):
            logger.info("unrefined_exists", key=key, bytes=len(body))
            return key
        r2_s3.put_bytes(
            STORAGE_UNREFINED_BUCKET_NAME,
            key,
            body,
            content_type="application/x-npz",
        )
        logger.info(
            "unrefined_saved",
            bucket=STORAGE_UNREFINED_BUCKET_NAME,
            key=key,
            bytes=len(body),
        )
        return key

    @classmethod
    def get_unrefined(cls, key: str) -> bytes:
        return r2_s3.get_bytes(STORAGE_UNREFINED_BUCKET_NAME, key)

    @classmethod
    def put_shard(
        cls,
        contract_id: str,
        transform_hash: str,
        split: TrainingSplit,
        index: int,
        body: bytes,
    ) -> str:
        """Hash body, skip upload if object already exists, return the key"""
        key = cls._shard_key(contract_id, transform_hash, split, index)
        r2_s3.put_bytes(
            STORAGE_SHARD_BUCKET_NAME,
            key,
            body,
            content_type="application/x-tar",
        )
        logger.info(
            "shard_saved",
            bucket=STORAGE_SHARD_BUCKET_NAME,
            key=key,
            bytes=len(body),
        )
        return key

    @classmethod
    def get_shard(cls, key: str) -> bytes:
        return r2_s3.get_bytes(STORAGE_SHARD_BUCKET_NAME, key)

    @classmethod
    def put_manifest(cls, contract_id: str, transform_hash: str, body: bytes) -> str:
        """Hash body, skip upload if object already exists, return the key"""
        key = cls._manifest_key(contract_id, transform_hash)
        r2_s3.put_bytes(
            STORAGE_SHARD_BUCKET_NAME,
            key,
            body,
            content_type="application/json",
        )
        logger.info(
            "manifest_saved",
            bucket=STORAGE_SHARD_BUCKET_NAME,
            key=key,
            bytes=len(body),
        )
        return key

    @classmethod
    def exists(cls, bucket: str, key: str) -> bool:
        return r2_s3.exists(bucket, key)
