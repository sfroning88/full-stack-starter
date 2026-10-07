"""
Author: Sean Froning
Created Date: 8.17.2026
Shared package unit test fixtures
"""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1]
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
