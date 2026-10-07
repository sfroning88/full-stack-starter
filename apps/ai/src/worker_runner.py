"""
Author: Sean Froning
Created Date: 8.17.2026
Worker runner for processing RQ jobs (queue name = WORKER_DOMAIN)
"""

import os
import sys
import signal
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_root / "src"))
sys.path.insert(0, str(_root))
from redis import Redis
from rq import Queue, Worker, SimpleWorker
from dotenv import load_dotenv
from fiery_python import config, logging, observability

logging.setup_structured_logging()
observability.configure_sentry()
logger = logging.get_logger(__name__)

script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, ".env")
load_dotenv(env_path)

redis_conn = Redis.from_url(config.get_required("redis"))
listen = [config.get_required("domain")]


def cleanup_on_shutdown(signum: int, _frame) -> None:
    """Graceful shutdown handler"""
    logger.info("Received signal, shutting down gracefully...", signal=signum)
    sys.exit(0)


if __name__ == "__main__":
    try:
        signal.signal(signal.SIGTERM, cleanup_on_shutdown)
        signal.signal(signal.SIGINT, cleanup_on_shutdown)
        queues = [Queue(name, connection=redis_conn) for name in listen]
        if not config.validate_required_services():
            logger.error("Required services are not available. Worker cannot start.")
            sys.exit(1)
        worker_class = os.getenv("RQ_WORKER_CLASS", "Worker")
        if worker_class == "SimpleWorker":
            worker = SimpleWorker(queues, connection=redis_conn)
            logger.info(
                "Worker initialized", worker_name=worker.name, mode="development"
            )
            logger.warning("SimpleWorker does not support parallel job processing")
        else:
            worker = Worker(queues, connection=redis_conn)
            logger.info(
                "Worker initialized", worker_name=worker.name, mode="production"
            )
        try:
            worker.work(with_scheduler=False)
        except KeyboardInterrupt:
            logger.info("Worker received shutdown signal")
    except Exception as err:
        logger.exception("Error in worker process", error=str(err))
        sys.exit(1)
