"""
Author: Sean Froning
Created Date: 8.19.2026
Definitions for Model structures
"""

from typing import List
from ..enums import ModelTier, ModelRole

MODEL_REGISTRY_SLOTS: List[tuple[ModelTier, ModelRole]] = [
    (ModelTier.CLOUD, ModelRole.SCREENER),
    (ModelTier.CLOUD, ModelRole.TEACHER),
    (ModelTier.EDGE, ModelRole.STUDENT),
]
MODEL_DB_FETCH_SIZE = 100
MODEL_DB_PAGE_SIZE = 1000
MODEL_TIER_ENUM = ("ai", "model_tier")
MODEL_ROLE_ENUM = ("ai", "model_role")
MODEL_METRIC_NAME_ENUM = ("ai", "model_metric_name")
MODEL_ARTIFACT_TABLE = ("ai", "model_artifact")
MODEL_METRIC_TABLE = ("ai", "model_metric")
MODEL_BUDGET_TABLE = ("ai", "model_budget")
MODEL_BUCKET_NAME = "models"
