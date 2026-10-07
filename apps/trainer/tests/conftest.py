"""
Author: Sean Froning
Created Date: 8.17.2026
Trainer unit test fixtures
"""

import sys
from pathlib import Path

TRAINER = Path(__file__).resolve().parents[1]
if str(TRAINER) not in sys.path:
    sys.path.insert(0, str(TRAINER))
