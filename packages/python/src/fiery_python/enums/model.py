"""
Author: Sean Froning
Created Date: 8.19.2026
Class definitions for Model enums
"""

from enum import Enum


class ModelTier(str, Enum):
    """Model Tier enumeration"""

    CLOUD = "cloud"
    EDGE = "edge"


class ModelRole(str, Enum):
    """Model Role enumeration"""

    SCREENER = "screener"
    TEACHER = "teacher"
    STUDENT = "student"


class ModelMetricName(str, Enum):
    """Model Metric Name enumeration"""

    ACCURACY = "accuracy"
    RECALL = "recall"
    PRECISION = "precision"
    FALSE_POSITIVE_RATE = "false_positive_rate"
    ABSTENTION_RATE = "abstention_rate"
    F1_SCORE = "f1_score"
    MACRO_F1_SCORE = "macro_f1_score"
