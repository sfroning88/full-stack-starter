"""
Author: Sean Froning
Created Date: 8.19.2026
Class definitions for Training enums
"""

from enum import Enum


class TrainingSplit(str, Enum):
    """Training Split enumeration"""

    TRAIN = "train"
    VALIDATE = "validate"
    TEST = "test"
    HOLDOUT = "holdout"


class TrainingSampleSource(str, Enum):
    """Training Sample Source enumeration"""

    HEPHAESTUS = "hephaestus"
    LICSAR = "licsar"
    OKADA = "okada"
    LLAIMA = "llaima"
    VILLARRICA = "villarrica"


class TrainingSignal(str, Enum):
    """Training Signal enumeration"""

    DEFORMATION = "deformation"
    SEISMIC = "seismic"


class TrainingStage(str, Enum):
    """Training Stage enumeration"""

    PRETRAIN = "pretrain"
    LORA = "lora"
    DISTILL = "distill"
    PRUNE = "prune"
    QUANTIZE = "quantize"


class TrainingStatus(str, Enum):
    """Training Status enumeration"""

    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TrainingPrecision(str, Enum):
    """Training Precision enumeration"""

    FP32 = "fp32"
    FP16 = "fp16"
    INT8 = "int8"


class TrainingSeismicLabel(str, Enum):
    """Training Seismic Label enumeration"""

    VT = "vt"
    LP = "lp"
    TR = "tr"
    TC = "tc"


class TrainingDeformationLabel(str, Enum):
    """Training Deformation Label enumeration"""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    UNCERTAIN = "uncertain"


class TrainingWindow(str, Enum):
    """Training Window enumeration"""

    HANN = "hann"
    HAMMING = "hamming"
    BLACKMAN = "blackman"
    BOXCAR = "boxcar"
    TUKEY = "tukey"


class TrainingNormalize(str, Enum):
    """Training Normalize enumeration"""

    MINMAX = "minmax"
    ZSCORE = "zscore"
    PERCENTILE = "percentile"
    NONE = "none"


class TrainingOptimizer(str, Enum):
    """Training Optimizer enumeration"""

    ADAM = "adam"
    ADAMW = "adamw"
    SGD = "sgd"
    RMSPROP = "rmsprop"


class TrainingRateSchedule(str, Enum):
    """Training Rate Schedule enumeration"""

    CONSTANT = "constant"
    COSINE = "cosine"
    STEP = "step"
    LINEAR = "linear"
    WARMUP_COSINE = "warmup_cosine"


class TrainingSparsitySchedule(str, Enum):
    """Training Sparsity Schedule enumeration"""

    LINEAR = "linear"
    CUBIC = "cubic"
    ONE_SHOT = "one_shot"


class TrainingPruningCriterion(str, Enum):
    """Training Pruning Criterion enumeration"""

    L1_MAGNITUDE = "l1_magnitude"
    L2_MAGNITUDE = "l2_magnitude"
    RANDOM = "random"
    MOVEMENT = "movement"


class TrainingQuantizeMethod(str, Enum):
    """Training Quantize Method enumeration"""

    PTQ = "ptq"
    QAT = "qat"


class TrainingDeformationSourceType(str, Enum):
    """Training Deformation Source Type enumeration"""

    MOGI = "mogi"
    OKADA = "okada"


class TrainingNoiseModel(str, Enum):
    """Training Noise Model enumeration"""

    NONE = "none"
    ATMOSPHERIC = "atmospheric"
    TURBULENT = "turbulent"
