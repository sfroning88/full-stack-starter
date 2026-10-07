"""
Author: Sean Froning
Created Date: 8.19.2026
Class definitions for Training enums
"""

from enum import Enum


class InferenceAbstainReason(str, Enum):
    """Inference Abstain Reason enumeration"""

    LOW_COHERENCE = "low_coherence"
    LOW_SNR = "low_snr"
    TRANSFORM_REJECTED = "transform_rejected"
    CONTRACT_MISMATCH = "contract_mismatch"
    LOW_CONFIDENCE = "low_confidence"
