#!/usr/bin/env python3
"""
Author: Sean Froning
Created Date: 10.7.2026
Unified test orchestrator for worker pipelines

Usage: python3 -m src.e2e.orchestrator <workflow>
Workflows: backend
Additional Kwargs:
    [backend] -timeout <seconds|none>

For example:
python3 -m src.e2e.orchestrator backend -timeout none
python3 -m src.e2e.orchestrator backend -timeout 300

Notes:
- Only Redis runs locally via Docker for the RQ queue.

Setup Steps:
1) pnpm use:local
2) pnpm redis:up
3) cd packages/python
4) python -m src.e2e.orchestrator

If Creating or Activating venv:
1) python3 -m venv .venv
2) source .venv/bin/activate
3) pip install -e .

Teardown: pnpm redis:down
"""

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv


def _find_root_env() -> str:
    """Walk up from this file to find monorepo root .env"""
    directory = Path(__file__).resolve().parent
    for _ in range(10):
        env_path = directory / ".env"
        if env_path.is_file():
            return str(env_path)
        directory = directory.parent
    return ""


load_dotenv(_find_root_env())

from .endpoints import WORKER_PORTS, worker_url
from .helpers import TESTS_DIR, seed_message_into_table, wait_for_health
from .container import clear_redis_queue, clear_postgres_db

MONOREPO_MARKER = "pnpm-workspace.yaml"
HEALTH_TIMEOUT_SECONDS = 120
SHARED_PYTHON_SRC = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    os.pardir,
    os.pardir,
    "src",
)

WORKER_APPS = {
    "backend": "apps/backend",
}


@dataclass(frozen=True)
class WorkerSpec:
    """Per-domain process plan for a workflow"""

    domain: str
    needs_rq_worker: bool


WORKFLOW_WORKERS: Dict[str, Tuple[WorkerSpec, ...]] = {
    "backend": (WorkerSpec(domain="backend", needs_rq_worker=True),),
}


def _find_monorepo_root() -> str:
    """Walk up from tests dir to find monorepo root"""
    directory = TESTS_DIR
    for _ in range(10):
        if os.path.isfile(os.path.join(directory, MONOREPO_MARKER)):
            return directory
        directory = os.path.dirname(directory)
    raise RuntimeError("Could not find monorepo root")


def _resolve_python(app_dir: str) -> str:
    """Return the app's .venv Python (fallback to current interpreter)"""
    candidate = os.path.join(app_dir, ".venv", "bin", "python")
    return candidate if os.path.isfile(candidate) else sys.executable


def _spawn_workers(root: str, specs: Tuple[WorkerSpec, ...]) -> List[subprocess.Popen]:
    """Spawn uvicorn (+ optional rq worker) per spec; return process handles"""
    procs: List[subprocess.Popen] = []
    for spec in specs:
        app_dir = os.path.join(root, WORKER_APPS[spec.domain])
        python = _resolve_python(app_dir)
        port = WORKER_PORTS[spec.domain]
        env = {**os.environ, "JOB_DOMAIN": spec.domain}
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = SHARED_PYTHON_SRC + (
            os.pathsep + existing if existing else ""
        )

        procs.append(
            subprocess.Popen(
                [python, "-m", "uvicorn", "src.main:app", "--port", str(port)],
                cwd=app_dir,
                env=env,
            )
        )

        if spec.needs_rq_worker:
            procs.append(
                subprocess.Popen(
                    [python, "-m", "src.worker_runner"],
                    cwd=app_dir,
                    env=env,
                )
            )
    return procs


def _kill_workers(procs: List[subprocess.Popen]) -> None:
    """Terminate all spawned worker processes"""
    for proc in procs:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass


def _pkill_workers() -> None:
    """Kill any lingering worker processes by command pattern (catches rq forks and restarts)"""
    for pattern in ["src.worker_runner", "uvicorn src.main:app"]:
        try:
            subprocess.run(["pkill", "-f", pattern], check=False)
        except Exception:
            pass


def _await_workers_ready(specs: Tuple[WorkerSpec, ...]) -> None:
    """Poll /health on each spawned API until 200 OK"""
    for spec in specs:
        base = worker_url(spec.domain)
        print(f"Waiting for {spec.domain} API @ {base} to become healthy...")
        if not wait_for_health(base, timeout=HEALTH_TIMEOUT_SECONDS):
            raise RuntimeError(f"{spec.domain} API never became healthy at {base}")
        print(f"{spec.domain} API ready")


_TIMEOUT_UNSET = object()


def _run_workflow(
    workflow: str,
    *,
    timeout: Any = _TIMEOUT_UNSET,
) -> None:
    """Dispatch to the script matching the workflow"""
    wait: Dict[str, Optional[int]] = (
        {} if timeout is _TIMEOUT_UNSET else {"timeout": timeout}
    )
    if workflow == "backend":
        from .scripts.backend import run_backend_test

        extra: Dict[str, Any] = dict(wait)
        run_backend_test(timeout=timeout, **extra)

    else:
        raise ValueError(f"Unknown workflow: {workflow}")


def _parse_timeout(parser: argparse.ArgumentParser, raw: Optional[str]) -> Any:
    """Return wait seconds, None for no timeout, or _TIMEOUT_UNSET if omitted"""
    if raw is None:
        return _TIMEOUT_UNSET
    if raw.lower() == "none":
        return None
    try:
        seconds = int(raw)
    except ValueError:
        parser.error("-timeout must be a positive integer or none")
    if seconds <= 0:
        parser.error("-timeout must be a positive integer or none")
    return seconds


def main() -> None:
    """CLI entry point - workflow argument is required"""
    parser = argparse.ArgumentParser(description="my-project unified test orchestrator")
    parser.add_argument(
        "workflow",
        choices=sorted(WORKFLOW_WORKERS.keys()),
        help="Test workflow to run",
    )
    parser.add_argument(
        "-timeout",
        metavar="SECONDS",
        help="wait timeout in seconds for ingest/refine/train/batch jobs, or none",
    )
    args = parser.parse_args()
    workflow: str = args.workflow
    timeout = _parse_timeout(parser, args.timeout)

    root = _find_monorepo_root()
    specs = WORKFLOW_WORKERS[workflow]

    procs = _spawn_workers(root, specs)
    print(f"Spawned {len(procs)} processes for {[spec.domain for spec in specs]}")

    try:
        _await_workers_ready(specs)
        clear_redis_queue()
        clear_postgres_db()
        seed_message_into_table()

        print(f"\n{'=' * 60}")
        print(f"Running {workflow} workflow")
        print(f"{'=' * 60}\n")

        if workflow == "train":
            from .helpers import ensure_trainer_deployed

            ensure_trainer_deployed(root)

        _run_workflow(
            workflow,
            timeout=timeout,
        )

        print(f"\n{'=' * 60}")
        print(f"{workflow.upper()} WORKFLOW PASSED")
        print(f"{'=' * 60}")

    except Exception as err:
        print(f"\n{'=' * 60}")
        print(f"{workflow.upper()} WORKFLOW FAILED: {err}")
        print(f"{'=' * 60}")
        raise

    finally:
        print("\nCleaning up...")
        try:
            clear_redis_queue()
            clear_postgres_db()
        except Exception as cleanup_err:
            print(f"WARNING: Redis cleanup failed: {cleanup_err}")
        _kill_workers(procs)
        _pkill_workers()
        print("Cleanup complete")


if __name__ == "__main__":
    main()
