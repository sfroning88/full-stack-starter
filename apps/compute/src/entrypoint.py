"""
Author: Sean Froning
Created Date: 10.7.2026
Main entrypoint for compute API
"""

import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).resolve().parent))

from my_python import logging

# Setup structured logging
logging.setup_structured_logging()
logger = logging.get_logger(__name__)


def entrypoint(_spec: Dict) -> Dict:
    logger.info("modal_app_launched")
    return {
        "ok": True,
    }
