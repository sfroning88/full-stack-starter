"""
Author: Sean Froning
Created Date: 8.29.2026
Send callback to apps/ai
"""

import time
import random
from typing import List
from fiery_python import logging
from fiery_python import ModelMetric

logger = logging.get_logger(__name__)

_MAX_CALLBACK_ATTEMPTS = 3


def send_callback(
    spec: dict,
    *,
    storage_path: str,
    signature: str,
    param_count: int,
    architecture: str,
    metrics: List[ModelMetric],
    decision: dict,
    hf_repo_id: str | None = None,
    hf_revision: str | None = None,
) -> None:
    import hashlib
    import hmac
    import json
    import httpx
    from fiery_python import ModelStorageServices

    callback_url = spec["callback_url"]
    if not callback_url or not isinstance(callback_url, str):
        raise RuntimeError("no_callback_url_in_spec")
    payload = {
        "session_id": spec["session_id"],
        "tier": spec["tier"],
        "role": spec["role"],
        "precision": spec["precision"],
        "storage_path": storage_path,
        "signature": signature,
        "param_count": param_count,
        "architecture": architecture,
        "sparsity": "0",
        "metrics": [metric.model_dump(mode="json") for metric in metrics],
        "nonce": spec.get("nonce") or "",
        "threshold": decision["threshold"],
        "abstention_band": decision["abstention_band"],
        "transform_hash": decision["transform_hash"],
        "op_version": decision["op_version"],
        "base_model_id": spec.get("base_model_id") or "",
        "revision": spec.get("revision") or "",
        "parent_id": spec.get("parent_id"),
        "hf_repo_id": hf_repo_id,
        "hf_revision": hf_revision,
    }
    canonical = json.dumps(
        {
            "architecture": architecture,
            "abstention_band": str(decision["abstention_band"]),
            "nonce": spec.get("nonce") or "",
            "op_version": decision["op_version"],
            "param_count": param_count,
            "precision": spec["precision"],
            "role": spec["role"],
            "session_id": spec["session_id"],
            "signature": signature,
            "sparsity": "0",
            "storage_path": storage_path,
            "threshold": str(decision["threshold"]),
            "tier": spec["tier"],
            "transform_hash": decision["transform_hash"],
            "base_model_id": spec.get("base_model_id") or "",
            "revision": spec.get("revision") or "",
            "parent_id": spec.get("parent_id") or "",
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    digest = hmac.new(
        ModelStorageServices._artifact_hmac_secret(),
        canonical,
        hashlib.sha256,
    ).hexdigest()
    for attempt in range(_MAX_CALLBACK_ATTEMPTS):
        try:
            response = httpx.post(
                callback_url,
                json=payload,
                headers={"X-Callback-Hmac": digest},
                timeout=30.0,
            )
            response.raise_for_status()
            break
        except Exception as err:
            logger.warning(
                "send_callback_failed",
                spec=spec["session_id"],
                attempt=attempt,
                error=str(err),
            )
            time.sleep(float(random.randint(10, 30)))
