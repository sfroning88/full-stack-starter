"""
Author: Sean Froning
Created Date: 8.21.2026
Ingest datasets testing script
"""

from typing import Any, Dict, List, Optional
from ..endpoints import INGEST_URL, endpoint_test
from ..helpers import wait_for_jobs
from ...fiery_python import TrainingSampleSource

_INGEST_SOURCES = (
    TrainingSampleSource.HEPHAESTUS,
    TrainingSampleSource.OKADA,
    TrainingSampleSource.LLAIMA,
)
_MAX_SAMPLES = 100
_JOB_TIMEOUT_SECONDS = 3000


def run_ingest_test(
    source: str,
    timeout: Optional[int] = _JOB_TIMEOUT_SECONDS,
    max_samples: int = _MAX_SAMPLES,
) -> None:
    """POST /api/ingest once for the chosen sample source"""
    print("Ingest integration endpoint test start")

    try:
        sample_source = TrainingSampleSource(source)
    except ValueError as err:
        raise ValueError("ingest requires -source hephaestus|okada|llaima") from err
    if sample_source not in _INGEST_SOURCES:
        raise ValueError("ingest requires -source hephaestus|okada|llaima")

    print(f"\nAttempting ingest for source: {sample_source.value}")

    response: Dict[str, Any] = endpoint_test(
        INGEST_URL,
        name=f"ingest_{sample_source.value}",
        payload={"source": sample_source.value, "max_samples": max_samples},
    )

    job_ids: List[str] = list(response.get("job_ids") or [])
    if not job_ids:
        raise RuntimeError(
            f"Ingest endpoint returned no job_ids for {sample_source.value}"
        )

    print(f"Enqueued {len(job_ids)} ingest job(s) for {sample_source.value}: {job_ids}")

    print(f"\nWaiting for {len(job_ids)} ingest job(s) to finish...")
    wait_for_jobs(job_ids, timeout=timeout)

    print("\nIngest integration testing complete")
