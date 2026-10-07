"""
Author: Sean Froning
Created Date: 8.28.2026
Type declarations for Training schema
"""

from typing import Optional, Tuple
from ..models import (
    TrainingHyperparameterPretrain,
    TrainingHyperparameterLora,
    TrainingHyperparameterDistill,
    TrainingHyperparameterPrune,
    TrainingHyperparameterQuantize,
    TrainingTargetModules,
)

TrainingHyperparameter = Tuple[
    Optional[TrainingHyperparameterPretrain],
    Optional[Tuple[TrainingHyperparameterLora, TrainingTargetModules]],
    Optional[TrainingHyperparameterDistill],
    Optional[TrainingHyperparameterPrune],
    Optional[TrainingHyperparameterQuantize],
]
