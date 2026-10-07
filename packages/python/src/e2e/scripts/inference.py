"""
Author: Sean Froning
Created Date: 8.28.2026
Inference backend testing script
"""

import requests
from typing import Any, Dict, List, Tuple
from ..endpoints import (
    INFERENCE_SINGLE_URL,
    endpoint_test,
)
from ..helpers import random_interferogram_id, random_seismic_event_id
from ...fiery_python import (
    MODEL_REGISTRY_SLOTS,
    ModelRole,
    ModelTier,
    TrainingSignal,
)


def run_inference_test(
    signal: str,
) -> Dict[Tuple[ModelTier, ModelRole], Dict[str, Any]]:
    """POST /api/inference/single per matching registry slot"""
    print("Inference integration endpoint test start")

    print(f"\nAttempting inference signal={signal}")

    if signal not in (
        TrainingSignal.DEFORMATION.value,
        TrainingSignal.SEISMIC.value,
    ):
        raise ValueError("inference requires -signal deformation|seismic")

    inferred: Dict[Tuple[ModelTier, ModelRole], Dict[str, Any]] = {}
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
        sample_key = "seismic_event_id"
        sample_id = random_seismic_event_id()
    else:
        slots = [
            key
            for key in MODEL_REGISTRY_SLOTS
            if key == (ModelTier.CLOUD, ModelRole.SCREENER)
        ]
        sample_key = "interferogram_id"
        sample_id = random_interferogram_id()

    for key in slots:
        tier, role = key
        print(f"\nPredicting with ({tier.value}, {role.value})")
        try:
            response: Dict[str, Any] = endpoint_test(
                INFERENCE_SINGLE_URL,
                name=f"inference_single_{tier.value}_{role.value}",
                payload={
                    "tier": tier.value,
                    "role": role.value,
                    sample_key: sample_id,
                },
            )
        except requests.HTTPError as err:
            print(
                f"WARNING: inference not ready for ({tier.value}, {role.value}): {err}"
            )
            inferred[key] = {"artifact_id": None, "ready": False}
            continue

        artifact_id = response.get("artifact_id")
        result = response.get("result") or []
        if not artifact_id or not result:
            print(
                f"WARNING: inference returned no prediction for "
                f"({tier.value}, {role.value}) artifact_id={artifact_id!r}"
            )
            inferred[key] = {"artifact_id": artifact_id, "ready": False}
            continue

        print(
            f"Inference complete for ({tier.value}, {role.value}) "
            f"artifact={artifact_id} result={result}"
        )
        inferred[key] = {"artifact_id": artifact_id, "ready": True}

    print("\nInference integration testing complete")
    return inferred
