"""
Author: Sean Froning
Created Date: 9.13.2026
Inference batch backend testing script
"""

from typing import Any, Dict, List, Optional, Tuple
from ..endpoints import INFERENCE_BATCH_URL, endpoint_test
from ..helpers import wait_for_jobs
from ...fiery_python import (
    MODEL_REGISTRY_SLOTS,
    ModelRole,
    ModelTier,
    TrainingSignal,
)

_JOB_TIMEOUT_SECONDS = 6000


def run_batch_test(
    signal: str,
    timeout: Optional[int] = _JOB_TIMEOUT_SECONDS,
) -> Dict[Tuple[ModelTier, ModelRole], Dict[str, Any]]:
    """POST /api/inference/batch per matching registry slot"""
    print("Batch inference integration endpoint test start")

    print(f"\nAttempting batch inference signal={signal}")

    if signal not in (
        TrainingSignal.DEFORMATION.value,
        TrainingSignal.SEISMIC.value,
    ):
        raise ValueError("batch requires -signal deformation|seismic")

    batched: Dict[Tuple[ModelTier, ModelRole], Dict[str, Any]] = {}
    if signal == TrainingSignal.SEISMIC.value:
        slots: List[Tuple[ModelTier, ModelRole]] = [
            key
            for key in MODEL_REGISTRY_SLOTS
            if key
            in (
                (ModelTier.CLOUD, ModelRole.TEACHER),
                (ModelTier.EDGE, ModelRole.STUDENT),
            )
        ]
    else:
        slots = [
            key
            for key in MODEL_REGISTRY_SLOTS
            if key == (ModelTier.CLOUD, ModelRole.SCREENER)
        ]

    for key in slots:
        tier, role = key
        print(f"\nEnqueueing batch for ({tier.value}, {role.value})")
        response: Dict[str, Any] = endpoint_test(
            INFERENCE_BATCH_URL,
            name=f"inference_batch_{tier.value}_{role.value}",
            payload={
                "tier": tier.value,
                "role": role.value,
            },
        )
        job_ids: List[str] = list(response.get("job_ids") or [])
        if not job_ids:
            raise RuntimeError(
                f"Batch endpoint returned no job_ids for ({tier.value}, {role.value})"
            )
        print(
            f"Enqueued {len(job_ids)} batch job(s) for "
            f"({tier.value}, {role.value}): {job_ids}"
        )
        print(f"\nWaiting for {len(job_ids)} batch job(s) to finish...")
        wait_for_jobs(job_ids, timeout=timeout)
        batched[key] = {"job_ids": job_ids, "ready": True}

    print("\nBatch inference integration testing complete")
    return batched
