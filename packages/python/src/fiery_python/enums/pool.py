"""
Author: Sean Froning
Created Date: 8.17.2026
Fetch mode for db_pool
"""

from enum import Enum


class PoolFetch(str, Enum):
    """Fetch pool enumeration"""

    NONE = "none"
    ONE = "one"
    ALL = "all"
