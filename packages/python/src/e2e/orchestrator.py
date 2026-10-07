#!/usr/bin/env python3
"""
Author: Sean Froning
Created Date: 8.26.2026
Unified test orchestrator for worker pipelines

Usage: python3 -m src.e2e.orchestrator <workflow>
Workflows: ingest|refine|train|promote|registry|inference|preview|batch
Additional Kwargs:
    [ingest] -source <hephaestus|okada|llaima>
    [refine] -shards <satellite|sensor
    [ingest|refine] -samples <max_samples>
    [train] -job <pretrain|lora|distill|prune|quantize>
    [inference|preview|batch] -signal <deformation|seismic>
    [ingest|refine|train|batch] -timeout <seconds|none>

For example:
python3 -m src.e2e.orchestrator ingest -source hephaestus -samples 10 -timeout none
python3 -m src.e2e.orchestrator refine -shards sensor -samples 10 -timeout 300
python3 -m src.e2e.orchestrator train -job lora -timeout none
python3 -m src.e2e.orchestrator inference -signal deformation
python3 -m src.e2e.orchestrator preview -signal deformation
python3 -m src.e2e.orchestrator batch -signal deformation -timeout 600

Notes:
- Tests run against the real Supabase project (tables + storage buckets).
  Tests run against the real Cloudlfare workspace (storage buckets).
  Tests run against the real Modal environment (app workspace).
- Postgres + buckets are Supabase/Cloudflare.
  Only Redis runs locally via Docker for the RQ queue.

Setup Steps:
1) pnpm use:local
2) pnpm redis:up
3) cd packages/python
4) python -m src.e2e.orchestrator <workflow> <**kwargs>

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
from .helpers import TESTS_DIR, wait_for_health
from .redis_clear import clear_redis_queue

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
    "ai": "apps/ai",
}


@dataclass(frozen=True)
class WorkerSpec:
    """Per-domain process plan for a workflow"""

    domain: str
    needs_rq_worker: bool


WORKFLOW_WORKERS: Dict[str, Tuple[WorkerSpec, ...]] = {
    "ingest": (WorkerSpec(domain="ai", needs_rq_worker=True),),
    "refine": (WorkerSpec(domain="ai", needs_rq_worker=True),),
    "train": (WorkerSpec(domain="ai", needs_rq_worker=True),),
    "promote": (WorkerSpec(domain="backend", needs_rq_worker=False),),
    "registry": (WorkerSpec(domain="backend", needs_rq_worker=False),),
    "inference": (WorkerSpec(domain="backend", needs_rq_worker=False),),
    "preview": (WorkerSpec(domain="backend", needs_rq_worker=False),),
    "batch": (WorkerSpec(domain="backend", needs_rq_worker=True),),
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
    source: Optional[str] = None,
    shards: Optional[str] = None,
    job: Optional[str] = None,
    signal: Optional[str] = None,
    samples: Optional[int] = None,
    timeout: Any = _TIMEOUT_UNSET,
) -> None:
    """Dispatch to the script matching the workflow"""
    wait: Dict[str, Optional[int]] = (
        {} if timeout is _TIMEOUT_UNSET else {"timeout": timeout}
    )
    if workflow == "ingest":
        from .scripts.ingest import run_ingest_test

        if not source:
            raise ValueError("ingest requires -source hephaestus|okada|llaima")
        extra: Dict[str, Any] = dict(wait)
        if samples is not None:
            extra["max_samples"] = samples
        run_ingest_test(source=source, **extra)
    elif workflow == "refine":
        from .scripts.refine import run_refine_test

        if not shards:
            raise ValueError("refine requires -shards satellite|sensor")
        extra: Dict[str, Any] = dict(wait)
        if samples is not None:
            extra["max_samples"] = samples
        run_refine_test(shards=shards, **extra)
    elif workflow == "train":
        from .scripts.train import run_train_test

        if not job:
            raise ValueError("train requires -job pretrain|lora|distill|prune|quantize")
        run_train_test(job=job, **wait)
    elif workflow == "promote":
        from .scripts.promote import run_promote_test

        run_promote_test()
    elif workflow == "registry":
        from .scripts.registry import run_reload_test

        run_reload_test()
    elif workflow == "inference":
        from .scripts.inference import run_inference_test

        if not signal:
            raise ValueError("inference requires -signal deformation|seismic")
        run_inference_test(signal=signal)
    elif workflow == "preview":
        from .scripts.preview import run_preview_test

        if not signal:
            raise ValueError("preview requires -signal deformation|seismic")
        run_preview_test(signal=signal)
    elif workflow == "batch":
        from .scripts.batch import run_batch_test

        if not signal:
            raise ValueError("batch requires -signal deformation|seismic")
        run_batch_test(signal=signal, **wait)
    else:
        raise ValueError(f"Unknown workflow: {workflow}")


def _resolve_kwargs(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Bind optional CLI flags to the workflow that owns them"""
    workflow = args.workflow
    source = args.source
    shards = args.shards
    if args.satellite:
        if shards and shards != "satellite":
            parser.error("use either -shards satellite or -satellite")
        shards = "satellite"
    if args.sensor:
        if shards and shards != "sensor":
            parser.error("use either -shards sensor or -sensor")
        shards = "sensor"
    if source is not None and workflow != "ingest":
        parser.error("-source is only valid for ingest")
    if args.samples is not None and workflow not in ("ingest", "refine"):
        parser.error("-samples is only valid for ingest, refine")
    if shards is not None and workflow != "refine":
        parser.error("-shards is only valid for refine")
    if args.job is not None and workflow != "train":
        parser.error("-job is only valid for train")
    if args.signal is not None and workflow not in ("inference", "batch", "preview"):
        parser.error("-signal is only valid for inference, batch, preview")
    if workflow == "ingest":
        if source is None:
            parser.error("ingest requires -source hephaestus|okada|llaima")
        if source not in ("hephaestus", "okada", "llaima"):
            parser.error("ingest requires -source hephaestus|okada|llaima")
    if workflow == "refine":
        if shards is None:
            parser.error("refine requires -shards satellite|sensor")
        if shards not in ("satellite", "sensor"):
            parser.error("refine requires -shards satellite|sensor")
    if workflow == "train" and args.job is None:
        parser.error("train requires -job pretrain|lora|distill|prune|quantize")
    if workflow == "inference" and args.signal is None:
        parser.error("inference requires -signal deformation|seismic")
    if workflow == "preview" and args.signal is None:
        parser.error("preview requires -signal deformation|seismic")
    if workflow == "batch" and args.signal is None:
        parser.error("batch requires -signal deformation|seismic")
    return source, shards, args.job, args.signal


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
    parser = argparse.ArgumentParser(
        description="fiery-spirit unified test orchestrator"
    )
    parser.add_argument(
        "workflow",
        choices=sorted(WORKFLOW_WORKERS.keys()),
        help="Test workflow to run",
    )
    parser.add_argument(
        "-source",
        choices=("hephaestus", "okada", "llaima"),
        help="[ingest] hephaestus|okada|llaima",
    )
    parser.add_argument(
        "-samples",
        type=int,
        metavar="MAX_SAMPLES",
        help="[ingest] max_samples for the ingest request",
    )
    parser.add_argument(
        "-shards",
        choices=("satellite", "sensor"),
        help="[refine] satellite interferograms or sensor waveforms",
    )
    parser.add_argument(
        "-satellite",
        action="store_true",
        help="[refine] alias for -shards satellite",
    )
    parser.add_argument(
        "-sensor",
        action="store_true",
        help="[refine] alias for -shards sensor",
    )
    parser.add_argument(
        "-job",
        choices=("pretrain", "lora", "distill", "prune", "quantize"),
        help="[train] training stage to spawn",
    )
    parser.add_argument(
        "-signal",
        choices=("deformation", "seismic"),
        help="[inference|preview|batch] interferogram or waveform sample",
    )
    parser.add_argument(
        "-timeout",
        metavar="SECONDS",
        help="wait timeout in seconds for ingest/refine/train/batch jobs, or none",
    )
    args = parser.parse_args()
    workflow: str = args.workflow
    source, shards, job, signal = _resolve_kwargs(parser, args)
    timeout = _parse_timeout(parser, args.timeout)
    samples = args.samples
    if samples is not None and samples <= 0:
        parser.error("-samples must be a positive integer")

    root = _find_monorepo_root()
    specs = WORKFLOW_WORKERS[workflow]

    procs = _spawn_workers(root, specs)
    print(f"Spawned {len(procs)} processes for {[spec.domain for spec in specs]}")

    try:
        _await_workers_ready(specs)
        clear_redis_queue()

        print(f"\n{'=' * 60}")
        print(f"Running {workflow} workflow")
        print(f"{'=' * 60}\n")

        if workflow == "train":
            from .helpers import ensure_trainer_deployed

            ensure_trainer_deployed(root)

        _run_workflow(
            workflow,
            source=source,
            shards=shards,
            job=job,
            signal=signal,
            samples=samples,
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
        except Exception as cleanup_err:
            print(f"WARNING: Redis cleanup failed: {cleanup_err}")
        _kill_workers(procs)
        _pkill_workers()
        print("Cleanup complete")


if __name__ == "__main__":
    main()
