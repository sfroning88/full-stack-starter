"""
Author: Sean Froning
Created Date: 8.22.2026
Refine shards testing script
"""

from typing import Any, List, Optional
from ..endpoints import REFINE_URL, endpoint_test
from ..helpers import wait_for_jobs
from ...fiery_python import (
    TRAINING_CONTRACT_DEFORMATION_VERSION,
    TRAINING_CONTRACT_SEISMIC_VERSION,
    UuidUtils,
)

_MAX_SAMPLES = 100
_JOB_TIMEOUT_SECONDS = 3000


def run_refine_test(
    shards: str,
    timeout: Optional[int] = _JOB_TIMEOUT_SECONDS,
    max_samples: int = _MAX_SAMPLES,
) -> None:
    """POST /api/refine once against R2 shards"""
    print("Refine integration endpoint test start")

    print(f"\nAttempting refine shards={shards}")

    if shards not in ("satellite", "sensor"):
        raise ValueError("refine requires -shards satellite|sensor")
    signal = "seismic" if shards == "sensor" else "deformation"
    version = (
        TRAINING_CONTRACT_SEISMIC_VERSION
        if shards == "sensor"
        else TRAINING_CONTRACT_DEFORMATION_VERSION
    )
    training_contract_id = UuidUtils.deterministic_uuid(signal, version)

    response: Any = endpoint_test(
        REFINE_URL,
        name=f"refine",
        payload={"contract_id": training_contract_id, "max_samples": max_samples},
    )

    job_ids: List[str] = list(response.get("job_ids") or [])
    if not job_ids:
        raise RuntimeError(f"Refine endpoint returned no job_ids")

    print(f"Enqueued {len(job_ids)} refine job(s): {job_ids}")

    print(f"\nWaiting for {len(job_ids)} refine job(s) to finish...")
    wait_for_jobs(job_ids, timeout=timeout)

    print("\nRefine integration testing complete")
