"""
Author: Sean Froning
Created Date: 8.21.2026
Model registry testing script
"""

from typing import Any, Dict, Tuple
from ..endpoints import (
    ML_RELOAD_URL,
    endpoint_test,
)
from ...fiery_python import (
    MODEL_REGISTRY_SLOTS,
    ModelRole,
    ModelTier,
)


def run_reload_test() -> Dict[Tuple[ModelTier, ModelRole], Dict[str, Any]]:
    """Simulate CRON: POST /api/ml/refresh per (tier, role) registry slot"""
    print("Model registry reload (CRON simulation) start")

    reloaded: Dict[Tuple[ModelTier, ModelRole], Dict[str, Any]] = {}
    for key in MODEL_REGISTRY_SLOTS:
        tier, role = key
        print(f"\nReloading registry for ({tier.value}, {role.value})")
        response: Dict[str, Any] = endpoint_test(
            ML_RELOAD_URL,
            name=f"ml_reload_{tier.value}_{role.value}",
            payload={"tier": tier.value, "role": role.value},
        )

        artifact_id = response.get("artifact_id")
        ready = bool(response.get("ready"))
        if response.get("tier") != tier.value or response.get("role") != role.value:
            raise RuntimeError(
                f"Reload response slot mismatch for ({tier.value}, {role.value}): {response}"
            )
        if not ready or not artifact_id:
            print(
                f"WARNING: registry reload not ready for ({tier.value}, {role.value}) "
                f"artifact_id={artifact_id!r} ready={ready}"
            )
        else:
            print(
                f"Registry reloaded for ({tier.value}, {role.value}) "
                f"artifact={artifact_id}"
            )
        reloaded[key] = {"artifact_id": artifact_id, "ready": ready}

    print("\nModel registry reload complete")
    return reloaded
