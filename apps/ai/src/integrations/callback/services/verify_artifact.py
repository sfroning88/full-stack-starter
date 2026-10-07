"""
Author: Sean Froning
Created Date: 8.24.2026
Operations pertaining to Callback verification
"""

import hashlib
import hmac
import json
from fiery_python import error
from fiery_python import ModelStorageServices
from ..schemas import CallbackRequest


class CallbackVerifyArtifact:
    """Persist artifact, metrics"""

    @staticmethod
    def verify_body_signature(payload: CallbackRequest, request_hmac: str) -> None:
        """HMAC-SHA256 of canonical JSON v MODELS_ARTIFACT_HMAC_KEY"""
        try:
            secret = ModelStorageServices._artifact_hmac_secret()
        except RuntimeError:
            raise error("MODELS_ARTIFACT_HMAC_KEY not configured")
        if not request_hmac:
            raise error("Callback HMAC missing", status_code=403)
        canonical = json.dumps(
            {
                "architecture": payload.architecture,
                "abstention_band": str(payload.abstention_band),
                "nonce": payload.nonce or "",
                "op_version": payload.op_version,
                "param_count": payload.param_count,
                "precision": payload.precision.value,
                "role": payload.role.value,
                "session_id": payload.session_id,
                "signature": payload.signature,
                "sparsity": str(payload.sparsity),
                "storage_path": payload.storage_path,
                "threshold": str(payload.threshold),
                "tier": payload.tier.value,
                "transform_hash": payload.transform_hash,
                "base_model_id": payload.base_model_id or "",
                "revision": payload.revision or "",
                "parent_id": payload.parent_id or "",
            },
            separators=(",", ":"),
            sort_keys=True,
        )
        expected = hmac.new(
            secret, canonical.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, request_hmac):
            raise error("Callback HMAC invalid", status_code=403)

    @staticmethod
    def verify_object_metadata(storage_path: str, signature: str) -> None:
        """HEAD models bucket; metadata artifact-hmac-sha256 must match signature"""
        try:
            stored = ModelStorageServices.head_hmac(storage_path)
        except Exception:
            raise error("Artifact object not found", status_code=403)
        if not hmac.compare_digest(stored, signature):
            raise error(
                "artifact-hmac-sha256 does not match HEAD models bucket",
                status_code=403,
            )
