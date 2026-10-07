"""
Author: Sean Froning
Created Date: 8.28.2026
Unit tests for Transformation interferogram preprocess
"""

from decimal import Decimal

import numpy as np
import pytest
from unittest.mock import patch
from fiery_python import (
    STORAGE_OP_VERSION,
    InferenceAbstainReason,
    TrainingDeformation,
    TrainingNormalize,
    TrainingSeismic,
    TrainingWindow,
    Transformation,
    TransformationRejected,
)


def _params(
    *,
    patch_px: int = 4,
    wrap_rad: str = "3.141592653589793",
    normalize: TrainingNormalize = TrainingNormalize.NONE,
    coherence_min: str = "0.3",
    class_id: str = "class-1",
) -> TrainingDeformation:
    return TrainingDeformation(
        patch_px=patch_px,
        wrap_rad=Decimal(wrap_rad),
        normalize=normalize,
        coherence_min=Decimal(coherence_min),
        class_id=class_id,
    )


def _seismic(
    *,
    nfft: int = 32,
    hop: int = 16,
    window: TrainingWindow = TrainingWindow.HANN,
    window_s: str = "1",
    sampling_hz: int = 100,
    mel_bins: int = 8,
    bandpass_low_hz: str = "1.00",
    bandpass_high_hz: str = "10.00",
    normalize: TrainingNormalize = TrainingNormalize.NONE,
    snr_min: str = "0.1",
    class_id: str = "class-1",
) -> TrainingSeismic:
    return TrainingSeismic(
        nfft=nfft,
        hop=hop,
        window=window,
        window_s=Decimal(window_s),
        sampling_hz=sampling_hz,
        mel_bins=mel_bins,
        bandpass_low_hz=Decimal(bandpass_low_hz),
        bandpass_high_hz=Decimal(bandpass_high_hz),
        normalize=normalize,
        snr_min=Decimal(snr_min),
        class_id=class_id,
    )


def _stack(phase: np.ndarray, coherence: np.ndarray) -> np.ndarray:
    return np.stack([phase, coherence]).astype(np.float32)


def _tone(samples: int = 100, hz: float = 5.0, sampling_hz: int = 100) -> np.ndarray:
    time = np.arange(samples, dtype=np.float32) / np.float32(sampling_hz)
    noise = (0.05 * np.sin(np.arange(samples, dtype=np.float32))).astype(np.float32)
    return np.sin(2.0 * np.pi * np.float32(hz) * time).astype(np.float32) + noise


def test_apply_wraps_and_center_crops_with_none_normalize():
    phase = np.full((8, 8), 4.0, dtype=np.float32)
    coherence = np.ones((8, 8), dtype=np.float32)
    wrap_rad = np.pi
    out = Transformation.apply_deformation(_stack(phase, coherence), _params())

    expected = np.mod(4.0 + wrap_rad, 2.0 * wrap_rad) - wrap_rad
    assert out.shape == (4, 4)
    np.testing.assert_allclose(out, expected, rtol=1e-5)


def test_apply_rejects_wrong_rank_or_channel_count():
    params = _params()
    with pytest.raises(TransformationRejected, match="\\(2, H, W\\)"):
        Transformation.apply_deformation(np.zeros((8, 8), dtype=np.float32), params)
    with pytest.raises(TransformationRejected, match="\\(2, H, W\\)"):
        Transformation.apply_deformation(np.zeros((3, 8, 8), dtype=np.float32), params)


def test_apply_rejects_array_smaller_than_patch():
    phase = np.zeros((2, 2), dtype=np.float32)
    coherence = np.ones((2, 2), dtype=np.float32)
    with pytest.raises(TransformationRejected, match="patch_px"):
        Transformation.apply_deformation(_stack(phase, coherence), _params(patch_px=4))


def test_apply_rejects_low_coherence():
    phase = np.zeros((8, 8), dtype=np.float32)
    coherence = np.full((8, 8), 0.1, dtype=np.float32)
    with pytest.raises(TransformationRejected, match="coherence"):
        Transformation.apply_deformation(_stack(phase, coherence), _params())


def test_apply_rejects_non_finite_coherence():
    phase = np.zeros((8, 8), dtype=np.float32)
    coherence = np.full((8, 8), np.nan, dtype=np.float32)
    with pytest.raises(TransformationRejected, match="non-finite"):
        Transformation.apply_deformation(_stack(phase, coherence), _params())


def test_apply_rejects_non_finite_phase():
    phase = np.full((8, 8), np.inf, dtype=np.float32)
    coherence = np.ones((8, 8), dtype=np.float32)
    with pytest.raises(TransformationRejected, match="non-finite"):
        Transformation.apply_deformation(_stack(phase, coherence), _params())


def test_apply_minmax_scales_crop_to_unit_interval():
    phase = np.zeros((8, 8), dtype=np.float32)
    phase[2:6, 2:6] = np.array(
        [
            [0.0, 1.0, 2.0, 3.0],
            [0.0, 1.0, 2.0, 3.0],
            [0.0, 1.0, 2.0, 3.0],
            [0.0, 1.0, 2.0, 3.0],
        ],
        dtype=np.float32,
    )
    coherence = np.ones((8, 8), dtype=np.float32)
    out = Transformation.apply_deformation(
        _stack(phase, coherence),
        _params(wrap_rad="1000", normalize=TrainingNormalize.MINMAX),
    )
    assert float(out.min()) == pytest.approx(0.0)
    assert float(out.max()) == pytest.approx(1.0)


def test_transform_hash_is_stable_and_ignores_class_id():
    first = Transformation.transform_hash_deformation(_params(class_id="a"))
    second = Transformation.transform_hash_deformation(_params(class_id="b"))
    assert first == second
    assert len(first) == 64


def test_transform_hash_changes_when_patch_px_changes():
    assert Transformation.transform_hash_deformation(
        _params(patch_px=4)
    ) != Transformation.transform_hash_deformation(_params(patch_px=8))


def test_transform_hash_includes_op_version():
    hashed = Transformation.transform_hash_deformation(_params())
    assert hashed == Transformation.transform_hash_deformation(_params())
    with patch(
        "fiery_python.ml.transformation.STORAGE_OP_VERSION",
        STORAGE_OP_VERSION + 1,
    ):
        assert hashed != Transformation.transform_hash_deformation(_params())


def test_map_rejection_to_reason_low_coherence():
    assert (
        Transformation.map_rejection_to_reason("coherence below min")
        is InferenceAbstainReason.LOW_COHERENCE
    )


def test_map_rejection_to_reason_transform_rejected():
    assert (
        Transformation.map_rejection_to_reason("expected array shape (2, H, W)")
        is InferenceAbstainReason.TRANSFORM_REJECTED
    )
    assert (
        Transformation.map_rejection_to_reason("snr below min")
        is InferenceAbstainReason.LOW_SNR
    )


def test_apply_seismic_squeezes_column_and_row_traces():
    tone = _tone()
    row = Transformation.apply_seismic(tone[None, :], _seismic())
    col = Transformation.apply_seismic(tone[:, None], _seismic())
    assert row.shape[0] == 1
    assert row.shape[1] == 8
    np.testing.assert_allclose(row, col, rtol=1e-5)


def test_apply_seismic_rejects_wrong_rank():
    with pytest.raises(TransformationRejected, match="\\(T,\\)"):
        Transformation.apply_seismic(np.ones((2, 100), dtype=np.float32), _seismic())


def test_apply_seismic_rejects_short_window():
    with pytest.raises(TransformationRejected, match="window_s"):
        Transformation.apply_seismic(_tone(samples=50), _seismic(window_s="1"))


def test_apply_seismic_rejects_non_finite_waveform():
    tone = _tone()
    tone[0] = np.nan
    with pytest.raises(TransformationRejected, match="non-finite waveform"):
        Transformation.apply_seismic(tone, _seismic())


def test_apply_seismic_rejects_invalid_sampling_hz():
    with pytest.raises(TransformationRejected, match="sampling_hz"):
        Transformation.apply_seismic(_tone(), _seismic(sampling_hz=0))


def test_apply_seismic_rejects_invalid_bandpass():
    with pytest.raises(TransformationRejected, match="bandpass"):
        Transformation.apply_seismic(
            _tone(), _seismic(bandpass_low_hz="1.00", bandpass_high_hz="80.00")
        )


def test_apply_seismic_rejects_constant_trace_snr():
    with pytest.raises(TransformationRejected, match="snr below min"):
        Transformation._require_snr(np.ones(100, dtype=np.float32), 0.1)


def test_apply_seismic_rejects_low_snr():
    with pytest.raises(TransformationRejected, match="snr below min"):
        Transformation.apply_seismic(_tone(), _seismic(snr_min="1000"))


def test_fixed_window_center_crops_long_trace():
    trace = np.arange(10, dtype=np.float32)
    cropped = Transformation._fixed_window(trace, Decimal("0.05"), 100)
    np.testing.assert_array_equal(cropped, np.array([2, 3, 4, 5, 6], dtype=np.float32))


def test_transform_hash_seismic_is_stable_and_ignores_class_id():
    first = Transformation.transform_hash_seismic(_seismic(class_id="a"))
    second = Transformation.transform_hash_seismic(_seismic(class_id="b"))
    assert first == second
    assert len(first) == 64
    assert first != Transformation.transform_hash_deformation(_params())


def test_transform_hash_seismic_changes_when_nfft_changes():
    assert Transformation.transform_hash_seismic(
        _seismic(nfft=32)
    ) != Transformation.transform_hash_seismic(_seismic(nfft=64))


def test_transform_hash_seismic_includes_op_version():
    hashed = Transformation.transform_hash_seismic(_seismic())
    with patch(
        "fiery_python.ml.transformation.STORAGE_OP_VERSION",
        STORAGE_OP_VERSION + 1,
    ):
        assert hashed != Transformation.transform_hash_seismic(_seismic())
