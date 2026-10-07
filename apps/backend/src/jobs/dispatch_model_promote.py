"""
Author: Sean Froning
Created Date: 8.26.2026
Cron job to model promote endpoint
"""

import asyncio
import httpx
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_root / "src"))
sys.path.insert(0, str(_root))
from fiery_python import config, logging

logger = logging.get_logger(__name__)

BACKEND_API_URL: str | None = config.get("BACKEND_API_URL")
AUTH_TOKEN: str | None = config.get("AUTH_TOKEN")

if not BACKEND_API_URL or not AUTH_TOKEN:
    raise RuntimeError("BACKEND_API_URL and AUTH_TOKEN must be configured")

HEADERS = {"auth-token": AUTH_TOKEN, "Content-Type": "application/json"}

WORKER_RETRIES: int = 3
WORKER_TIMEOUT: float = 600


async def main():
    async with httpx.AsyncClient() as client:
        endpoint = "/api/ml/promote"
        for attempt in range(WORKER_RETRIES):
            try:
                response = await client.post(
                    f"{BACKEND_API_URL}{endpoint}",
                    headers=HEADERS,
                    json={},
                    timeout=WORKER_TIMEOUT,
                )
            except httpx.RequestError:
                if attempt == WORKER_RETRIES - 1:
                    raise
                await asyncio.sleep(2**attempt)
                continue
            if response.status_code < 500 and response.status_code != 429:
                response.raise_for_status()
                request_id = response.headers.get(
                    "x-request-id"
                ) or response.headers.get("x-correlation-id")
                logger.info(
                    "dispatch_model_promote_completed",
                    endpoint=endpoint,
                    status_code=response.status_code,
                    request_id=request_id,
                )
                break
            if attempt == WORKER_RETRIES - 1:
                response.raise_for_status()
            await asyncio.sleep(2**attempt)


if __name__ == "__main__":
    asyncio.run(main())
