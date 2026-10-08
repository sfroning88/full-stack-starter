"""
Author: Sean Froning
Created Date: 10.7.2026
Backend testing script
"""

from typing import Any, Dict, List, Optional
from ..endpoints import MESSAGE_URL, endpoint_test
from ..helpers import wait_for_jobs

_JOB_TIMEOUT_SECONDS = 6000


def run_backend_test(
    timeout: Optional[int] = _JOB_TIMEOUT_SECONDS,
) -> None:
    """POST /api/message to print message"""
    print("Backend integration endpoint test start")

    print(f"\nAttempting to print message")

    response: Dict[str, Any] = endpoint_test(
        MESSAGE_URL,
        name=f"backend_message",
        payload={},
    )
    job_ids: List[str] = list(response.get("job_ids") or [])
    if not job_ids:
        raise RuntimeError(f"Backend endpoint returned no job_ids")
    print(f"Enqueued {len(job_ids)} message job(s)")

    print(f"\nWaiting for {len(job_ids)} batch job(s) to finish...")
    wait_for_jobs(job_ids, timeout=timeout)

    print("\nBackend integration testing complete")
