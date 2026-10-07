"""
Author: Sean Froning
Created Date: 8.17.2026
Number field validator utils
"""

import math
import pandas as pd
from typing import Tuple


class NumberUtils:
    """Field serializers for numbers"""

    @staticmethod
    def _to_float(value) -> float:
        """Coerce Decimal / Optional / numeric to float, treating None as NaN"""
        if value is None:
            return float("nan")
        try:
            return float(value)
        except (TypeError, ValueError):
            return float("nan")

    @staticmethod
    def clamp_decimal(value: float, precision: int, scale: int) -> float:
        """Clamp a float to the valid range of a Decimal(precision, scale) column"""
        if value is None or math.isnan(value):
            raise ValueError("clamp_decimal received NaN/None")
        integer_digits = precision - scale
        limit = 10**integer_digits - 10**-scale
        if math.isinf(value):
            return limit if value > 0 else -limit
        return max(-limit, min(limit, round(value, scale)))

    @staticmethod
    def encode_cyclical(ordinal: int) -> Tuple[float, float]:
        if ordinal is None or math.isnan(ordinal):
            raise ValueError("encode_cyclical received NaN/None")
        month = pd.Timestamp.fromordinal(ordinal).month
        angle = 2.0 * math.pi * month / 12.0
        return math.sin(angle), math.cos(angle)
