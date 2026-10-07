"""
Author: Sean Froning
Created Date: 9.21.2026
Save checkpoint to HuggingFace
"""

import time
import random
from fiery_python import logging

logger = logging.get_logger(__name__)

_MAX_CHECKPOINT_ATTEMPTS = 3


def save_checkpoint(
    spec: dict,
    *,
    storage_path: str,
    weights_bytes: bytes,
    sidecar: dict,
) -> dict:
    from fiery_python import HubCheckpointServices, MlflowUtils, ModelTier, ModelRole

    if not weights_bytes or not isinstance(weights_bytes, bytes):
        logger.warning(
            "save_checkpoint_skipped",
            spec=spec.get("session_id"),
            error="missing weights_bytes",
        )
        return sidecar
    try:
        tier = ModelTier(spec["tier"])
        role = ModelRole(spec["role"])
        hf_repo_id = MlflowUtils.hf_repo_id(tier, role)
    except (ValueError, EnvironmentError, KeyError) as err:
        logger.warning("save_checkpoint_failed", error=str(err))
        return sidecar
    for attempt in range(_MAX_CHECKPOINT_ATTEMPTS):
        try:
            hf_revision = HubCheckpointServices.push_commit(
                storage_path, weights_bytes, sidecar, repo_id=hf_repo_id
            )
            sidecar["hf_repo_id"] = hf_repo_id
            sidecar["hf_revision"] = hf_revision
            return sidecar
        except Exception as err:
            logger.warning(
                "save_checkpoint_failed",
                spec=spec["session_id"],
                attempt=attempt,
                error=str(err),
            )
            time.sleep(float(random.randint(10, 30)))
    return sidecar
