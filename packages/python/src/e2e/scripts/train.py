"""
Author: Sean Froning
Created Date: 8.23.2026
Train spawn testing script
"""

"""
Special note for running training jobs:
    1) cloudflared tunnel --url http://localhost:8001
    2) copy temporary url as AI_API_URL
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from ..endpoints import TRAIN_URL, endpoint_test
from ..helpers import latest_artifact_id, wait_for_jobs, wait_for_session
from ...fiery_python import (
    TRAINING_CONTRACT_DEFORMATION_VERSION,
    TRAINING_CONTRACT_SEISMIC_VERSION,
    ModelRole,
    ModelTier,
    Transformation,
    TrainingStage,
    TrainingNormalize,
    TrainingWindow,
    TrainingDeformation,
    TrainingSeismic,
    UuidUtils,
)

_JOB_TIMEOUT_SECONDS = 6000


def run_train_test(job: str, timeout: Optional[int] = _JOB_TIMEOUT_SECONDS) -> None:
    """POST /api/train once against chosen spawn; wait for callback"""
    print("Train integration endpoint test start")

    print(f"\nAttempting train job={job}")

    try:
        stage = TrainingStage(job)
    except ValueError as err:
        raise ValueError(
            "train requires -job pretrain|lora|distill|prune|quantize"
        ) from err
    if stage is TrainingStage.LORA:
        deformation = TrainingDeformation(
            patch_px=8,
            wrap_rad=Decimal("3.14159"),
            normalize=TrainingNormalize.NONE,
            coherence_min=Decimal("0.300"),
            class_id="ignored-for-hash",
        )
        transform_hash = Transformation.transform_hash_deformation(deformation)
        training_contract_id = UuidUtils.deterministic_uuid(
            "deformation", TRAINING_CONTRACT_DEFORMATION_VERSION
        )
    else:
        seismic = TrainingSeismic(
            nfft=256,
            hop=128,
            window=TrainingWindow.HANN,
            window_s=Decimal("60.000"),
            sampling_hz=100,
            mel_bins=64,
            bandpass_low_hz=Decimal("1.00"),
            bandpass_high_hz=Decimal("10.00"),
            normalize=TrainingNormalize.NONE,
            snr_min=Decimal("0.300"),
            class_id="ignored-for-hash",
        )
        transform_hash = Transformation.transform_hash_seismic(seismic)
        training_contract_id = UuidUtils.deterministic_uuid(
            "seismic", TRAINING_CONTRACT_SEISMIC_VERSION
        )
    dataset_version_id = UuidUtils.deterministic_uuid(
        training_contract_id, transform_hash
    )

    payload: Dict[str, Any] = {
        "contract_id": training_contract_id,
        "version_id": dataset_version_id,
        "stage": stage,
    }
    if stage is TrainingStage.DISTILL:
        payload["parent_id"] = latest_artifact_id(
            ModelTier.CLOUD, ModelRole.TEACHER, TrainingStage.PRETRAIN
        )
    elif stage is TrainingStage.PRUNE:
        payload["parent_id"] = latest_artifact_id(
            ModelTier.EDGE, ModelRole.STUDENT, TrainingStage.DISTILL
        )
    elif stage is TrainingStage.QUANTIZE:
        payload["parent_id"] = latest_artifact_id(
            ModelTier.EDGE, ModelRole.STUDENT, TrainingStage.PRUNE
        )

    response: Any = endpoint_test(
        TRAIN_URL,
        name=f"train_{stage.value}",
        payload=payload,
    )

    job_ids: List[str] = list(response.get("job_ids") or [])
    if not job_ids:
        raise RuntimeError(f"Train endpoint returned no job_ids")

    session_id = response.get("session_id")
    if not session_id or not isinstance(session_id, str):
        raise RuntimeError("Train endpoint returned no session_id")

    print(f"Enqueued {len(job_ids)} train job(s): {job_ids}")

    print(f"\nWaiting for {len(job_ids)} train job(s) to finish...")
    wait_for_jobs(job_ids, timeout=timeout)

    print(f"\nWaiting for {session_id} train session to send callback...")
    wait_for_session(session_id, timeout=timeout)

    print("\nTrain integration testing complete")
