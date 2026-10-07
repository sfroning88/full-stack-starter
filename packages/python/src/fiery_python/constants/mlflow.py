"""
Author: Sean Froning
Created Date: 9.21.2026
Definitions for mlflow processes
"""

from ..enums import ModelTier, ModelRole

MLFLOW_REGISTERED_MODELS = {
    (ModelTier.CLOUD, ModelRole.SCREENER): "Fiery-Screener",
    (ModelTier.CLOUD, ModelRole.TEACHER): "Fiery-Teacher",
    (ModelTier.EDGE, ModelRole.STUDENT): "Fiery-Student",
}
