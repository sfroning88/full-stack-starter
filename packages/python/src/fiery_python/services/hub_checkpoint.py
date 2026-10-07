"""
Author: Sean Froning
Created Date: 9.21.2026
HuggingFace Hub model checkpointing
"""

import io
import json
from datetime import datetime, timezone
from huggingface_hub import CommitOperationAdd, HfApi
from ..core import config, logging
from .model_storage import ModelStorageServices

logger = logging.get_logger(__name__)

HF_TOKEN = config.get("HF_TOKEN")


class HubCheckpointServices:
    """HuggingFace Hub model checkpointing services shared across writer (trainer) and reader (callback)"""

    @staticmethod
    def push_commit(
        weights_key: str, weights_bytes: bytes, sidecar: dict, *, repo_id: str
    ) -> str:
        if not HF_TOKEN or not isinstance(HF_TOKEN, str):
            raise EnvironmentError("misconfigured HF_TOKEN")
        session_id = (sidecar.get("spec") or {}).get("session_id") or weights_key
        if not session_id or not isinstance(session_id, str):
            raise RuntimeError("malformed session_id from sidecar")
        sidecar_key = ModelStorageServices.sidecar_key(weights_key)
        sidecar_body = json.dumps(
            sidecar, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        api = HfApi(token=HF_TOKEN)
        api.create_repo(
            repo_id=repo_id,
            repo_type="model",
            private=True,
            exist_ok=True,
        )
        committed_at = datetime.now(timezone.utc)
        commit_message = f"{str(session_id)}_{committed_at}"
        commit = api.create_commit(
            repo_id=repo_id,
            repo_type="model",
            operations=[
                CommitOperationAdd(
                    path_in_repo=weights_key,
                    path_or_fileobj=io.BytesIO(weights_bytes),
                ),
                CommitOperationAdd(
                    path_in_repo=sidecar_key,
                    path_or_fileobj=io.BytesIO(sidecar_body),
                ),
            ],
            commit_message=commit_message,
        )
        return commit.oid
