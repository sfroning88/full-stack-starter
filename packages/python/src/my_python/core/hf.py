"""
Author: Sean Froning
Created Date: 10.7.2026
Process-local Hugging Face Hub client
"""

from typing import Optional
from huggingface_hub import HfApi
from .config import config
from ..resources import SyncLazyResource


class _HuggingFace:
    """Lazy Hugging Face Hub client bound to HF_TOKEN"""

    def __init__(self) -> None:
        self._client = SyncLazyResource(self._build_client)

    def _token(self) -> str:
        token = config.get("HF_TOKEN")
        if not token or not isinstance(token, str):
            raise EnvironmentError("misconfigured HF_TOKEN")
        return token

    def _build_client(self) -> HfApi:
        return HfApi(token=self._token())

    def get_client(self) -> HfApi:
        """Lazy-load shared Hub client (cached per worker process)"""
        return self._client.get()

    def reset(self) -> None:
        """Drop the cached client so a forked child rebuilds its own"""
        self._client.reset()

    def namespace(self) -> Optional[str]:
        value = config.get("HF_MODEL_NAMESPACE")
        if not value or not isinstance(value, str):
            return None
        return value

    def repo_id(self, name: str) -> str:
        """Prefix a repo name with HF_MODEL_NAMESPACE when it is set"""
        namespace = self.namespace()
        if namespace:
            return f"{namespace}/{name}"
        return name


hf = _HuggingFace()
