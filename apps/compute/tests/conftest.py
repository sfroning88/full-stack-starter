"""
Author: Sean Froning
Created Date: 10.7.2026
Compute unit test fixtures
"""

import sys
from pathlib import Path

COMPUTE = Path(__file__).resolve().parents[1]
if str(COMPUTE) not in sys.path:
    sys.path.insert(0, str(COMPUTE))
