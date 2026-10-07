"""
Author: Sean Froning
Created Date: 8.17.2026
Redis queue manager with connection pooling
"""

import time
from typing import Any, Dict, List
from redis import Redis, ConnectionPool
from rq import Queue
from rq.job import Job
from .config import config
from .logging import logging
from ..resources import SyncLazyResource

logger = logging.get_logger(__name__)

JOB_TIMEOUT = 3600
REDIS_MAX_CONNECTIONS = 20


class _Queue:

    def __init__(self) -> None:
        self._pool = SyncLazyResource(self._build_pool)
        self._rq = SyncLazyResource(self._build_rq)

    def _build_pool(self) -> ConnectionPool:
        """Build the Redis connection pool once on first access"""
        pool = ConnectionPool.from_url(
            config.get_required("redis"),
            max_connections=REDIS_MAX_CONNECTIONS,
            retry_on_timeout=True,
            socket_keepalive=True,
        )
        Redis(connection_pool=pool).ping()
        return pool

    def _build_rq(self) -> Queue:
        """Build the RQ queue once on first access (queue name = WORKER_DOMAIN)"""
        return Queue(config.get_required("domain"), connection=self.get_connection())

    def get_connection(self) -> Redis:
        """Return a Redis client backed by the shared connection pool"""
        return Redis(connection_pool=self._pool.get())

    def enqueue_jobs(self, jobs: List[Dict[str, Any]]) -> List[Job]:
        enqueued, failures = [], []
        rq = self._rq.get()
        for job_data in jobs:
            try:
                func = job_data["func"]
                args = job_data.get("args", [])
                tags = job_data.get("tags")
                job_kwargs = {
                    "job_timeout": job_data.get("job_timeout", JOB_TIMEOUT),
                    "job_id": job_data.get("job_id"),
                    "meta": job_data.get("metadata") or {},
                }
                if tags:
                    job = rq.enqueue(func, *args, tags=tags, **job_kwargs)
                else:
                    job = rq.enqueue(func, *args, **job_kwargs)
                func_name = (
                    getattr(func, "__name__", None)
                    or getattr(func, "__qualname__", None)
                    or str(func)
                )
                logger.info(
                    "job_enqueued", job_id=job.id, queue=rq.name, func=func_name
                )
                enqueued.append(job)
            except Exception as err:
                failures.append({"job_id": job_data.get("job_id"), "error": str(err)})
                logger.error(
                    "job_enqueue_failed", job_id=job_data.get("job_id"), error=str(err)
                )
        if failures:
            raise RuntimeError(f"{len(failures)} jobs failed to enqueue")
        return enqueued

    def close(self) -> None:
        """Close shared Redis connection pool during shutdown"""
        pool = self._pool.pop()
        self._rq.reset()
        if pool is not None:
            pool.disconnect()
            logger.info("Redis connection pool closed")

    def reset(self) -> None:
        """Drop the cached pool and queue so a forked child rebuilds its own"""
        self._pool.reset()
        self._rq.reset()

    def clear(self) -> Dict[str, int]:
        """Purge all queued and failed jobs for this worker domain"""
        rq = self._rq.get()
        queued = rq.empty()
        failed_registry = rq.failed_job_registry
        failed_ids = failed_registry.get_job_ids()
        for job_id in failed_ids:
            failed_registry.remove(job_id, delete_job=True)
        logger.info(
            "queue_cleared", queue=rq.name, queued=queued, failed=len(failed_ids)
        )
        return {"queued": queued, "failed": len(failed_ids)}

    def health_check(self) -> Dict[str, Any]:
        try:
            conn = self.get_connection()
            start = time.time()
            conn.ping()
            ping_ms = (time.time() - start) * 1000
            rq = self._rq.get()
            queued = len(rq)
            failed = len(rq.failed_job_registry)
            status = (
                "healthy" if failed < 50 else "warning" if failed < 100 else "critical"
            )
            return {
                "status": status,
                "redis": {"connected": True, "ping_ms": round(ping_ms, 2)},
                "queued": queued,
                "failed": failed,
            }
        except Exception as err:
            logger.error("queue_health_check_failed", error=str(err))
            return {"status": "unhealthy", "error": str(err)}


queue = _Queue()
