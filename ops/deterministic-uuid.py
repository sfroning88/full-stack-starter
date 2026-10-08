#!/usr/bin/env python3
"""
Author: Sean Froning
Created Date: 10.7.2026
Print deterministic uuid
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "packages" / "python" / "src"))

from my_python import (
    MyClass,
    UuidUtils,
)

my_class = MyClass(message="hello")


print(f"my_class.id = {UuidUtils.deterministic_uuid(*my_class)}")
