"""
Author: Sean Froning
Created Date: 8.20.2026
S3-backed sidecar safetensors storage for trained models
"""

import hashlib
import hmac
import json
import os
from safetensors.torch import save, load
from typing import Tuple, Union, assert_never
from ..constants import MODEL_BUCKET_NAME
from ..core import logging, models_s3

logger = logging.get_logger(__name__)

_ARTIFACT_HMAC_META_KEY = "artifact-hmac-sha256"
_WEIGHTS_SUFFIX = ".safetensors"
_SIDECAR_SUFFIX = ".json"


class ModelStorageServices:
    """S3-backed sidecar safetensors storage shared across training (writer) and inference (reader)"""

    @staticmethod
    def _artifact_hmac_secret() -> bytes:
        raw = os.environ.get("MODELS_ARTIFACT_HMAC_KEY")
        if not raw:
            raise RuntimeError("MODELS_ARTIFACT_HMAC_KEY is not configured")
        return raw.encode("utf-8")

    @classmethod
    def _artifact_hmac_hex(cls, body: bytes) -> str:
        return hmac.new(cls._artifact_hmac_secret(), body, hashlib.sha256).hexdigest()

    @classmethod
    def head_hmac(cls, key: str) -> str:
        """HEAD models bucket; return artifact-hmac-sha256 or raise"""
        obj = models_s3.head_object(MODEL_BUCKET_NAME, key)
        meta = obj.get("Metadata") or {}
        expected = meta.get(_ARTIFACT_HMAC_META_KEY)
        if not expected:
            raise RuntimeError(
                f"Model object {key!r} missing {_ARTIFACT_HMAC_META_KEY} metadata",
            )
        return expected

    @classmethod
    def sidecar_key(cls, weights_key: str) -> str:
        if weights_key.endswith(_WEIGHTS_SUFFIX):
            return weights_key[: -len(_WEIGHTS_SUFFIX)] + _SIDECAR_SUFFIX
        raise ValueError("weights key must end with .safetensors")

    @classmethod
    def _get_verified_bytes(cls, key: str) -> bytes:
        obj = models_s3.get_object(MODEL_BUCKET_NAME, key)
        stream = obj["Body"]
        try:
            body = stream.read()
        finally:
            stream.close()
        meta = obj.get("Metadata") or {}
        expected = meta.get(_ARTIFACT_HMAC_META_KEY)
        if not expected:
            raise RuntimeError(
                f"Model object {key!r} missing {_ARTIFACT_HMAC_META_KEY} metadata",
            )
        computed = cls._artifact_hmac_hex(body)
        if not hmac.compare_digest(expected, computed):
            raise RuntimeError(f"Model artifact HMAC verification failed for {key!r}")
        logger.info("model_loaded", key=key, bytes=len(body))
        return body

    @classmethod
    def save_artifact(
        cls,
        body_or_weights: Union[bytes, dict],
        sidecar: dict,
        weights_key: str,
    ) -> str:
        """Serialize payload with body/dict + sidecar and upload to s3://{MODEL_BUCKET_NAME}/{key}"""
        if not body_or_weights:
            raise ValueError("missing required body_or_weights")
        body = None
        weights = None
        if isinstance(body_or_weights, bytes):
            body = body_or_weights
        elif isinstance(body_or_weights, dict):
            weights = save(body_or_weights)
        else:
            assert_never(body_or_weights)
        sig = cls._artifact_hmac_hex(body or weights)
        sidecar = {**sidecar, "weights_hmac": sig}
        models_s3.put_bytes(
            MODEL_BUCKET_NAME,
            weights_key,
            body or weights,
            content_type="application/octet-stream",
            metadata={_ARTIFACT_HMAC_META_KEY: sig},
        )
        cls.put_sidecar(weights_key, sidecar)
        return weights_key

    @classmethod
    def put_sidecar(cls, weights_key: str, sidecar: dict) -> str:
        sidecar_body = json.dumps(
            sidecar, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        sidecar_key = cls.sidecar_key(weights_key)
        models_s3.put_bytes(
            MODEL_BUCKET_NAME,
            sidecar_key,
            sidecar_body,
            content_type="application/json",
            metadata={_ARTIFACT_HMAC_META_KEY: cls._artifact_hmac_hex(sidecar_body)},
        )
        return sidecar_key

    @classmethod
    def load_artifact(
        cls,
        weights_key: str,
        *,
        is_body: bool = False,
        is_weights: bool = False,
    ) -> Tuple[Union[bytes, dict], dict]:
        """Download body/weights from bucket, verify HMAC metadata, then deserialize with state_dict"""
        if (not is_body and not is_weights) or (is_body and is_weights):
            raise RuntimeError("malformed body or weights call")
        body = None
        weights = None
        if is_body:
            body = cls._get_verified_bytes(weights_key)
        elif is_weights:
            weights = cls._get_verified_bytes(weights_key)
        sidecar_body = cls._get_verified_bytes(cls.sidecar_key(weights_key))
        sidecar = json.loads(sidecar_body.decode("utf-8"))
        if not hmac.compare_digest(
            sidecar.get("weights_hmac", ""), cls.head_hmac(weights_key)
        ):
            raise RuntimeError("sidecar weights_hmac does not match object HEAD")
        return body or load(weights), sidecar
