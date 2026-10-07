#!/usr/bin/env python3
"""
Author: Sean Froning
Created Date: 8.31.2026
Print deterministic uuid
"""

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "packages" / "python" / "src"))

from fiery_python import (
    STORAGE_OP_VERSION,
    TRAINING_CONTRACT_DEFORMATION_VERSION,
    TRAINING_CONTRACT_SEISMIC_VERSION,
    TrainingNormalize,
    TrainingWindow,
    TrainingDeformation,
    TrainingSeismic,
    UuidUtils,
)

_LOG_MEL_EPS = 1e-10
_BANDPASS_ORDER = 10

DEFORMATION_CONTRACT = (
    "deformation",
    TRAINING_CONTRACT_DEFORMATION_VERSION,
)

SEISMIC_CONTRACT = (
    "seismic",
    TRAINING_CONTRACT_SEISMIC_VERSION,
)

deformation = TrainingDeformation(
    patch_px=8,
    wrap_rad=Decimal("3.14159"),
    normalize=TrainingNormalize.NONE,
    coherence_min=Decimal("0.300"),
    class_id="ignored-for-hash",
)


seismic = TrainingSeismic(
    nfft=256,
    hop=128,
    window=TrainingWindow.HANN,
    window_s=Decimal("60.000"),
    sampling_hz=100,
    mel_bins=64,
    bandpass_low_hz=Decimal("1.00"),
    bandpass_high_hz=Decimal("10.00"),
    normalize=TrainingNormalize.NONE,
    snr_min=Decimal("0.300"),
    class_id="ignored-for-hash",
)


def transform_hash_deformation(training_deformation: TrainingDeformation) -> str:
    """SHA-256 of sorted deformation transformations and source of apply"""
    payload = {
        "op_version": STORAGE_OP_VERSION,
        "patch_px": training_deformation.patch_px,
        "wrap_rad": str(training_deformation.wrap_rad),
        "normalize": training_deformation.normalize.value,
        "coherence_min": str(training_deformation.coherence_min),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def transform_hash_seismic(training_seismic: TrainingSeismic) -> str:
    """SHA-256 of sroted seismic transformations and source of apply"""
    payload = {
        "op_version": STORAGE_OP_VERSION,
        "signal": "seismic",
        "nfft": training_seismic.nfft,
        "hop": training_seismic.hop,
        "window": training_seismic.window.value,
        "window_s": str(training_seismic.window_s),
        "sampling_hz": training_seismic.sampling_hz,
        "mel_bins": training_seismic.mel_bins,
        "bandpass_low_hz": str(training_seismic.bandpass_low_hz),
        "bandpass_high_hz": str(training_seismic.bandpass_high_hz),
        "bandpass_order": _BANDPASS_ORDER,
        "normalize": training_seismic.normalize.value,
        "snr_min": str(training_seismic.snr_min),
        "log_mel_eps": str(_LOG_MEL_EPS),
        "array_shape": "1,M,F",
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


_TRANSFORM_HASH_DEFORMATION = transform_hash_deformation(deformation)
_TRANSFORM_HASH_SEISMIC = transform_hash_seismic(seismic)


DEFORMATION_VERSION = (
    "0aab32fe-c404-5a06-83af-ee87a5043085",
    _TRANSFORM_HASH_DEFORMATION,
)

SEISMIC_VERSION = (
    "0aab32fe-c404-5a06-83af-ee87a5043085",
    _TRANSFORM_HASH_SEISMIC,
)


print(f"deformation_contract = {UuidUtils.deterministic_uuid(*DEFORMATION_CONTRACT)}")
print(f"deformation_hash = {_TRANSFORM_HASH_DEFORMATION}")
print(f"deformation_dataset = {UuidUtils.deterministic_uuid(*DEFORMATION_VERSION)}")


print(f"seismic_contract = {UuidUtils.deterministic_uuid(*SEISMIC_CONTRACT)}")
print(f"seismic_hash = {_TRANSFORM_HASH_SEISMIC}")
print(f"seismic_dataset = {UuidUtils.deterministic_uuid(*SEISMIC_VERSION)}")
