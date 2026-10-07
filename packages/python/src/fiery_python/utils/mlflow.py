"""
Author: Sean Froning
Created Date: 9.21.2026
mlflow process utils
"""

from ..core import config
from ..constants import MLFLOW_REGISTERED_MODELS
from ..enums import ModelTier, ModelRole


class MlflowUtils:
    """mlflow helpers"""

    @staticmethod
    def hf_repo_id(tier: ModelTier, role: ModelRole) -> str:
        HF_MODEL_NAMESPACE = config.get("HF_MODEL_NAMESPACE")
        if not HF_MODEL_NAMESPACE or not isinstance(HF_MODEL_NAMESPACE, str):
            raise EnvironmentError("misconfigured HF_MODEL_NAMESPACE")
        name = MLFLOW_REGISTERED_MODELS[(tier, role)]
        return f"{HF_MODEL_NAMESPACE}/{name}"
