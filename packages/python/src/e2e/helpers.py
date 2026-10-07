"""
Author: Sean Froning
Created Date: 8.21.2026
Shared utility helpers for tests
"""

import io
import os
import numpy as np
import shutil
import subprocess
import time as Time
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image

import requests
from psycopg2 import sql
from rq.job import Job

from fiery_python import (
    db_pool,
    queue,
    PoolFetch,
    ModelRole,
    ModelTier,
    TrainingStage,
)
from ..fiery_python import (
    MODEL_ARTIFACT_TABLE,
    MODEL_ROLE_ENUM,
    MODEL_TIER_ENUM,
    TRAINING_INTERFEROGRAM_TABLE,
    TRAINING_SEISMIC_EVENT_TABLE,
    TRAINING_SESSION_TABLE,
    TRAINING_STAGE_ENUM,
    TRAINING_STATUS_ENUM,
    TrainingStatus,
)

TESTS_DIR = os.path.dirname(__file__)

INGEST_PRESET_PATH = os.path.join(TESTS_DIR, "presets", "ingest.txt")

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
ASCII_RAMP = " .:-=+*#%@"


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


def ensure_trainer_deployed(root: str) -> None:
    """Deploy apps/trainer so AI can Function.from_name + spawn"""
    if os.environ.get("MODAL_SKIP_DEPLOY") == "1":
        print("Skipping Modal deploy (MODAL_SKIP_DEPLOY=1)")
        return
    trainer_dir = os.path.join(root, "apps", "trainer")
    modal = shutil.which("modal")
    command = [modal, "deploy", "modal_app.py"]
    print(f"Deploying fiery-trainer from {trainer_dir}")
    result = subprocess.run(
        command,
        cwd=trainer_dir,
        env=os.environ.copy(),
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "Modal deploy failed; token, Fiery-Environment secret, "
            "and modal CLI must already exist in this workspace"
        )


_SELECT_SESSION_STATUS = sql.SQL("""
    SELECT status::{status_enum}
    FROM {table}
    WHERE id = %s::uuid
""").format(
    table=sql.Identifier(*TRAINING_SESSION_TABLE),
    status_enum=sql.Identifier(*TRAINING_STATUS_ENUM),
)


def _select_session_status(session_id: str) -> Optional[TrainingStatus]:
    """Read training_session.status; None if missing or query failed"""
    row = db_pool.run(
        _SELECT_SESSION_STATUS,
        (session_id,),
        fetch=PoolFetch.ONE,
        error_event="fetch_training_session_status_failed",
        reraise=False,
    )
    if not row:
        print("Session is None; will retry...")
        return None
    if isinstance(row, str):
        value = row
    elif isinstance(row, Dict):
        value = row.get("status")
    elif isinstance(row, List[Dict]):
        value = row[0].get("status")
    else:
        value = None
    if value is None:
        print("Value is None; will retry...")
        return None
    return TrainingStatus(value)


def wait_for_session(
    session_id: str, timeout: Optional[int] = 3600, interval: float = 120.0
) -> None:
    """Block until training session is completed; timeout None waits forever"""
    deadline = None if timeout is None else Time.time() + timeout
    while True:
        status = _select_session_status(session_id)
        if status is TrainingStatus.COMPLETED:
            print(f"Session {session_id} completed")
            return
        if status is TrainingStatus.FAILED:
            raise RuntimeError(f"session {session_id} failed")
        if status is TrainingStatus.CANCELLED:
            raise RuntimeError(f"session {session_id} cancelled")
        if deadline is not None and Time.time() >= deadline:
            raise RuntimeError(f"session {session_id} timed out after {timeout}s")
        Time.sleep(interval)


_SELECT_LATEST_ARTIFACT = sql.SQL("""
    SELECT id::text
    FROM {table}
    WHERE tier = %s::{tier_enum}
        AND role = %s::{role_enum}
        AND stage = %s::{stage_enum}
    ORDER BY created_at DESC
    LIMIT 1
""").format(
    table=sql.Identifier(*MODEL_ARTIFACT_TABLE),
    tier_enum=sql.Identifier(*MODEL_TIER_ENUM),
    role_enum=sql.Identifier(*MODEL_ROLE_ENUM),
    stage_enum=sql.Identifier(*TRAINING_STAGE_ENUM),
)


_SELECT_RANDOM_INTERFEROGRAM = sql.SQL("""
    SELECT id::text
    FROM {table}
    WHERE volcano_id IS NOT NULL
    ORDER BY RANDOM()
    LIMIT 1
""").format(table=sql.Identifier(*TRAINING_INTERFEROGRAM_TABLE))

_SELECT_RANDOM_SEISMIC_EVENT = sql.SQL("""
    SELECT id::text
    FROM {table}
    WHERE volcano_id IS NOT NULL
    ORDER BY RANDOM()
    LIMIT 1
""").format(table=sql.Identifier(*TRAINING_SEISMIC_EVENT_TABLE))


def _select_random_id(
    query: Any,
    error_event: str,
    empty_message: str,
    params: Optional[Tuple] = None,
) -> str:
    row = db_pool.run(
        query,
        params,
        fetch=PoolFetch.ONE,
        error_event=error_event,
        reraise=False,
    )
    if not row or not isinstance(row, dict) or not row.get("id"):
        raise RuntimeError(empty_message)
    return str(row["id"])


def latest_artifact_id(tier: ModelTier, role: ModelRole, stage: TrainingStage) -> str:
    """Newest model_artifact.id for (tier, role, stage) as train parent_id"""
    return _select_random_id(
        _SELECT_LATEST_ARTIFACT,
        "fetch_model_artifact_failed",
        f"No {tier.value} {role.value} {stage.value} model_artifact for parent_id",
        (tier.value, role.value, stage.value),
    )


def random_interferogram_id() -> str:
    """Random training_interferogram.id for deformation inference"""
    return _select_random_id(
        _SELECT_RANDOM_INTERFEROGRAM,
        "fetch_training_interferogram_failed",
        "No training_interferogram row for deformation inference",
    )


def random_seismic_event_id() -> str:
    """Random training_seismic_event.id for seismic inference"""
    return _select_random_id(
        _SELECT_RANDOM_SEISMIC_EVENT,
        "fetch_training_seismic_event_failed",
        "No training_seismic_event row for seismic inference",
    )


def print_ascii(png: bytes, columns: int = 64) -> None:
    gray = np.asarray(Image.open(io.BytesIO(png)).convert("L"))
    height, width = gray.shape
    scale = max(1, width // columns)
    shrink = gray[:: scale * 2, ::scale]
    ramp = np.array(list(ASCII_RAMP))
    idx = (shrink.astype(np.float32) / 255 * (len(ASCII_RAMP) - 1)).astype(int)
    print(f"preview {width}x{height} png bytes={len(png)}")
    for row in idx:
        print("".join(ramp[row]))
