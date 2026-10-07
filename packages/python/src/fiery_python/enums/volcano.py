"""
Author: Sean Froning
Created Date: 8.19.2026
Class definitions for Volcano enums
"""

from enum import Enum


class VolcanoZone(str, Enum):
    """Volcano Zone enumeration"""

    SVZ = "svz"
    CVZ = "cvz"
    NVZ = "nvz"
    AVZ = "avz"
    OTHER = "other"


class VolcanoActivitySource(str, Enum):
    """Volcano Activity Source enumeration"""

    GVP = "gvp"
    SERNAGEOMIN = "sernageomin"
    MANUAL = "manual"


class VolcanoAlertLevel(str, Enum):
    """Volcano Alert Level enumeration"""

    GREEN = "green"
    YELLOW = "yellow"
    ORANGE = "orange"
    RED = "red"
