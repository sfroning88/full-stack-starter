"""
Author: Sean Froning
Created Date: 10.7.2026
Shared utility helpers for tests
"""

import os
import time as Time
from typing import List, Optional, Tuple

import requests
from psycopg2 import sql
from rq.job import Job

from my_python import (
    db_pool,
    queue,
    PoolFetch,
    MyClass,
    MY_TABLE,
)

TESTS_DIR = os.path.dirname(__file__)


def wait_for_job_completion(job_id: str, timeout: Optional[int] = 600) -> bool:
    """Wait for Redis job to complete before proceeding; timeout None waits forever"""
    try:
        job = Job.fetch(job_id, connection=queue.get_connection())
        if job is None:
            print(f"Job {job_id} not found")
            return False
        start_time = Time.time()
        while job.get_status() in ["queued", "started"]:
            if timeout is not None and Time.time() - start_time > timeout:
                print(f"Job {job_id} timed out after {timeout} seconds")
                return False
            Time.sleep(1)
            job.refresh()
        final_status = job.get_status()
        if final_status == "finished":
            print(f"Job {job_id} completed successfully")
            return True
        if final_status == "failed":
            print(f"Job {job_id} failed: {job.exc_info}")
            return False
        print(f"Job {job_id} ended with status: {final_status}")
        return False
    except Exception as err:
        print(f"Error waiting for job {job_id}: {str(err)}")
        return False


def load_preset_lines(preset_path: str) -> List[str]:
    """Load non-comment non-empty lines from a preset file"""
    try:
        with open(preset_path, encoding="utf-8") as file:
            return [
                line.strip()
                for line in file.readlines()
                if line.strip() and not line.startswith("#")
            ]
    except OSError as err:
        raise RuntimeError(f"Could not read {preset_path}: {err}") from err


def load_preset_sections(preset_path: str) -> Tuple[List[str], List[str]]:
    """Split preset on '---' delimiter into (input_lines, config_lines)"""
    lines = load_preset_lines(preset_path)
    if "---" in lines:
        idx = lines.index("---")
        return lines[:idx], lines[idx + 1 :]
    return lines, []


def resolve_local_preset_path(raw: str) -> str:
    """Expand and normalize a preset file path relative to tests dir"""
    path = os.path.expanduser(os.path.expandvars(raw.strip()))
    if os.path.isabs(path):
        return os.path.normpath(path)
    return os.path.normpath(os.path.join(TESTS_DIR, path))


def wait_for_health(base_url: str, timeout: int = 30, interval: float = 0.5) -> bool:
    """Poll a worker /health endpoint until 200 OK or timeout"""
    deadline = Time.time() + timeout
    last_err: str = ""
    while Time.time() < deadline:
        try:
            response = requests.get(f"{base_url}/health", timeout=2)
            if response.status_code == 200:
                return True
            last_err = f"status={response.status_code}"
        except requests.RequestException as err:
            last_err = str(err)
        Time.sleep(interval)
    print(f"Health check timed out for {base_url} ({last_err})")
    return False


def wait_for_jobs(job_ids: List[str], timeout: Optional[int] = 6000) -> None:
    """Block until every job_id reports finished; raise if any fail/timeout"""
    failures: List[str] = []
    for job_id in job_ids:
        if not wait_for_job_completion(job_id, timeout=timeout):
            failures.append(job_id)
    if failures:
        raise RuntimeError(f"{len(failures)} job(s) did not complete: {failures}")


_SEED_MESSAGE_SQL = sql.SQL("""
    INSERT INTO {table} 
    (
        id,
        message,
        created_at,
        updated_at,
    )
    VALUES (
        %(id)s::uuid,
        %(message),
        NOW(),
        NOW(),
    )
    ON CONFLICT (id)
    DO UPDATE SET
        message = EXCLUDED.message
        updated_at = EXCLUDED.updated_at
""").format(table=sql.Identifier(*MY_TABLE))


def seed_message_into_table() -> None:
    my_class = MyClass()
    my_class.id = MyClass.deterministic_id()
    if not my_class.id:
        raise ValueError("failed to create deterministic_id")
    db_pool.run(
        _SEED_MESSAGE_SQL,
        my_class.prepare_for_storage(include_id=True),
    )
