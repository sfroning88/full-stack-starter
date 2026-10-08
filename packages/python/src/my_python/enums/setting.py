"""
Author: Sean Froning
Created Date: 10.7.2026
Class definitions for Setting enums
"""

from enum import Enum


class DomainOption(str, Enum):
    """Worker domain enumeration"""

    API = "api"
