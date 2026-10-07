"""
Author: Sean Froning
Created Date: 9.14.2026
Preview backend testing script
"""

from typing import Any, Dict

import requests

from ..endpoints import PREVIEW_URL, endpoint_bytes
from ..helpers import (
    random_interferogram_id,
    random_seismic_event_id,
    PNG_MAGIC,
    print_ascii,
)
from ...fiery_python import TrainingSignal


def run_preview_test(signal: str) -> Dict[str, Any]:
    """POST /api/preview and print a CLI rendering of the PNG"""
    print("Preview integration endpoint test start")
    print(f"\nAttempting preview signal={signal}")

    if signal not in (
        TrainingSignal.DEFORMATION.value,
        TrainingSignal.SEISMIC.value,
    ):
        raise ValueError("preview requires -signal deformation|seismic")

    if signal == TrainingSignal.SEISMIC.value:
        sample_key = "seismic_event_id"
        sample_id = random_seismic_event_id()
    else:
        sample_key = "interferogram_id"
        sample_id = random_interferogram_id()

    print(f"\nLoading preview for {sample_key}={sample_id}")
    try:
        png = endpoint_bytes(
            PREVIEW_URL,
            name=f"preview_{signal}",
            payload={sample_key: sample_id},
        )
    except requests.HTTPError as err:
        print(f"WARNING: preview not ready: {err}")
        return {"sample_id": sample_id, "ready": False}

    if not png.startswith(PNG_MAGIC):
        print(f"WARNING: preview returned non-png bytes={len(png)}")
        return {"sample_id": sample_id, "ready": False}

    print_ascii(png)
    print("\nPreview integration testing complete")
    return {"sample_id": sample_id, "ready": True, "bytes": len(png)}
