"""
Author: Sean Froning
Created Date: 8.17.2026
Configuration for fiery_python
"""

import os
from dotenv import load_dotenv

load_dotenv()

REQUIRED_ENV = {
    "database": "DATABASE_URL",
    "redis": "REDIS_URL",
    "domain": "JOB_DOMAIN",
    "backend_api_url": "BACKEND_API_URL",
    "ai_api_url": "AI_API_URL",
    "token": "AUTH_TOKEN",
}


class _Config:
    """Centralized environment config"""

    def get(self, key: str, default=None):
        return os.getenv(key, default)

    def _required_key_to_var(self, key: str) -> str:
        if key not in REQUIRED_ENV.keys():
            raise ValueError(f"Bad key {key} for required env")
        return os.getenv(REQUIRED_ENV.get(key))

    def get_required(self, key: str) -> str:
        val = self._required_key_to_var(key)
        if not val:
            raise ValueError(f"Required env {key} not set")
        return val

    def get_log_format(self) -> str:
        return self.get("LOG_FORMAT") or "console"

    def get_db_pool_min(self) -> int:
        return int(self.get("DB_POOL_MIN") or 2)

    def get_db_pool_max(self) -> int:
        return int(self.get("DB_POOL_MAX") or 10)

    def get_required_services_status(self) -> dict[str, bool]:
        return {name: bool(os.getenv(var)) for name, var in REQUIRED_ENV.items()}

    def validate_required_services(self) -> bool:
        return all(self.get_required_services_status().values())


config = _Config()
