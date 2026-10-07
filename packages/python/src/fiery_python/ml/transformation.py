"""
Author: Sean Froning
Created Date: 8.28.2026
Deterministic interferogram preprocess for deformation shards
"""

import hashlib
import json
import numpy as np
from decimal import Decimal
from scipy.signal import butter, sosfilt
from scipy.signal.windows import tukey
from typing import Tuple, assert_never
from ..constants import STORAGE_OP_VERSION
from ..enums import InferenceAbstainReason, TrainingNormalize, TrainingWindow
from ..models import TrainingDeformation, TrainingSeismic

_LOG_MEL_EPS = 1e-10
_BANDPASS_ORDER = 10


class TransformationRejected(ValueError):
    """Sample failed coherence_min (or shape) and prevent from entering shard"""


class Transformation:
    """Pure wrap / crop / normalize over (phase, coherence) stacks"""

    @staticmethod
    def _split_channels(array: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Require float32 (2, H, W): channel 0 phase, channel 1 coherence"""
        if array.ndim != 3 or array.shape[0] != 2:
            raise TransformationRejected("expected array shape (2, H, W)")
        return array[0], array[1]

    @staticmethod
    def _center_crop(array: np.ndarray, patch_px: int) -> np.ndarray:
        """Center crop to patch_px; reject if either side is smaller"""
        if patch_px <= 0:
            raise TransformationRejected("patch_px must be postive int")
        height, width = array.shape[-2], array.shape[-1]
        if height < patch_px or width < patch_px:
            raise TransformationRejected("array smaller than patch_px")
        top = (height - patch_px) // 2
        left = (width - patch_px) // 2
        return array[top : top + patch_px, left : left + patch_px]

    @staticmethod
    def _as_waveform(array: np.ndarray) -> np.ndarray:
        """Require float32 (T,): channel 0 Time"""
        trace = np.squeeze(np.asarray(array, dtype=np.float32))
        if trace.ndim != 1 or trace.size <= 0:
            raise TransformationRejected("expected array shape (T,)")
        return trace

    @staticmethod
    def _fixed_window(
        trace: np.ndarray, window_s: Decimal, sampling_hz: int
    ) -> np.ndarray:
        """Crop to sampling window"""
        seconds = float(window_s)
        if not np.isfinite(seconds) or seconds <= 0:
            raise TransformationRejected("window_s must be positive finite")
        target = int(round(seconds * sampling_hz))
        if target <= 0:
            raise TransformationRejected("window_s must be positive finite")
        if trace.size < target:
            raise TransformationRejected("waveform shorter than window_s")
        if trace.size == target:
            return trace
        start = (trace.size - target) // 2
        return trace[start : start + target]

    @staticmethod
    def _bandpass_filter(
        trace: np.ndarray, sampling_hz: int, low_hz: float, high_hz: float
    ) -> np.ndarray:
        """Run through nyquist sampling frequency; bandpass filter"""
        nyquist = sampling_hz / 2.0
        if not (0 < low_hz < high_hz < nyquist):
            raise TransformationRejected("bandpass bounds invalid")
        sos = butter(
            _BANDPASS_ORDER,
            (low_hz, high_hz),
            btype="bandpass",
            fs=sampling_hz,
            output="sos",
        )
        return sosfilt(sos, trace).astype(np.float32)

    @staticmethod
    def _require_snr(trace: np.ndarray, snr_min: float) -> None:
        """Require sampling noise rate to be valid"""
        if not np.isfinite(snr_min) or snr_min < 0:
            raise TransformationRejected("snr_min must be finite nonnegative")
        rms = float(np.sqrt(np.mean(np.square(trace))))
        mad = float(np.median(np.abs(trace - np.median(trace))))
        noise = 1.4826 * mad
        if noise <= 0:
            raise TransformationRejected("snr below min")
        if rms / noise < snr_min:
            raise TransformationRejected("snr below min")

    @staticmethod
    def _stft_window(kind: TrainingWindow, nfft: int) -> np.ndarray:
        """Fit to training_window"""
        match kind:
            case TrainingWindow.HANN:
                return np.hanning(nfft).astype(np.float32)
            case TrainingWindow.HAMMING:
                return np.hamming(nfft).astype(np.float32)
            case TrainingWindow.BLACKMAN:
                return np.blackman(nfft).astype(np.float32)
            case TrainingWindow.BOXCAR:
                return np.ones(nfft, dtype=np.float32)
            case TrainingWindow.TUKEY:
                return tukey(nfft, 0.5).astype(np.float32)
            case _:
                assert_never(kind)

    @classmethod
    def _log_mel(
        cls,
        trace: np.ndarray,
        sampling_hz: int,
        nfft: int,
        hop: int,
        window: TrainingWindow,
        mel_bins: int,
        low_hz: float,
        high_hz: float,
    ) -> np.ndarray:
        if nfft <= 0 or hop <= 0 or mel_bins <= 0:
            raise TransformationRejected("stft params must be positive int")
        if trace.size < nfft:
            raise TransformationRejected("waveform shorter than nfft")
        n_frames = 1 + (trace.size - nfft) // hop
        if n_frames < 1:
            raise TransformationRejected("waveform shorter than nfft")
        tapers = cls._stft_window(window, nfft)
        frames = np.lib.stride_tricks.sliding_window_view(trace, nfft)[::hop][:n_frames]
        power = np.abs(np.fft.rfft(frames * tapers, n=nfft, axis=1)) ** 2
        n_fft_bins = nfft // 2 + 1
        mel_low = 2595.0 * np.log10(1.0 + low_hz / 700.0)
        mel_high = 2595.0 * np.log10(1.0 + high_hz / 700.0)
        mel_points = np.linspace(mel_low, mel_high, mel_bins + 2)
        hz_points = 700.0 * (10.0 ** (mel_points / 2595.0) - 1.0)
        bins = np.floor((nfft + 1) * hz_points / sampling_hz).astype(np.int64)
        bins = np.clip(bins, 0, n_fft_bins - 1)
        bank = np.zeros((mel_bins, n_fft_bins), dtype=np.float32)
        for index in range(mel_bins):
            left = int(bins[index])
            center = int(bins[index + 1])
            right = int(bins[index + 2])
            if center <= left:
                center = min(left + 1, n_fft_bins - 1)
            if right <= center:
                right = min(center + 1, n_fft_bins - 1)
            for bin_index in range(left, center):
                bank[index, bin_index] = (bin_index - left) / (center - left)
            for bin_index in range(center, right):
                bank[index, bin_index] = (right - bin_index) / (right - center)
        log_mel = np.log(power @ bank.T + _LOG_MEL_EPS).astype(np.float32)
        return np.expand_dims(log_mel.T, axis=0)

    @staticmethod
    def _normalize(array: np.ndarray, normalize: TrainingNormalize) -> np.ndarray:
        """Apply TrainingNormalize; PERCENTILE uses fixed 2-98 clips"""
        match normalize:
            case TrainingNormalize.NONE:
                return array
            case TrainingNormalize.MINMAX:
                low, high = float(np.min(array)), float(np.max(array))
                if high <= low:
                    raise TransformationRejected("minmax range is empy")
                return (array - low) / (high - low)
            case TrainingNormalize.ZSCORE:
                mean, std = float(np.mean(array)), float(np.std(array))
                if std == 0.0:
                    raise TransformationRejected("zscore std is zero")
                return (array - mean) / std
            case TrainingNormalize.PERCENTILE:
                low, high = np.percentile(array, (2.0, 98.0))
                low, high = float(low), float(high)
                if high <= low:
                    raise TransformationRejected("percentile range is empty")
                clipped = np.clip(array, low, high)
                return (clipped - low) / (high - low)
            case _:
                assert_never(normalize)

    @classmethod
    def apply_deformation(
        cls, array: np.ndarray, training_deformation: TrainingDeformation
    ) -> np.ndarray:
        """Deterministic preprocess: wrap, crop, normalize; raise if incoherent"""
        phase, coherence = cls._split_channels(array)
        if not (np.isfinite(phase).all() and np.isfinite(coherence).all()):
            raise TransformationRejected("non-finite phase or coherence")
        if float(np.mean(coherence)) < float(training_deformation.coherence_min):
            raise TransformationRejected("coherence below min")
        wrap_rad = float(training_deformation.wrap_rad)
        if not np.isfinite(wrap_rad) or wrap_rad <= 0:
            raise TransformationRejected("wrap_rad must be positive finite")
        wrapped = np.mod(phase + wrap_rad, 2.0 * wrap_rad) - wrap_rad
        cropped = cls._center_crop(wrapped, training_deformation.patch_px)
        return cls._normalize(cropped, training_deformation.normalize)

    @classmethod
    def apply_seismic(
        cls, array: np.ndarray, training_seismic: TrainingSeismic
    ) -> np.ndarray:
        """Deterministic preprocess: wrap, crop, normalize; raise if incoherent"""
        trace = cls._as_waveform(array)
        if not np.isfinite(trace).all():
            raise TransformationRejected("non-finite waveform")
        sampling_hz = training_seismic.sampling_hz
        if sampling_hz <= 0:
            raise TransformationRejected("sampling_hz must be positive int")
        windowed = cls._fixed_window(trace, training_seismic.window_s, sampling_hz)
        filtered = cls._bandpass_filter(
            windowed,
            sampling_hz,
            float(training_seismic.bandpass_low_hz),
            float(training_seismic.bandpass_high_hz),
        )
        cls._require_snr(filtered, float(training_seismic.snr_min))
        spec = cls._log_mel(
            filtered,
            sampling_hz,
            training_seismic.nfft,
            training_seismic.hop,
            training_seismic.window,
            training_seismic.mel_bins,
            float(training_seismic.bandpass_low_hz),
            float(training_seismic.bandpass_high_hz),
        )
        return cls._normalize(spec, training_seismic.normalize).astype(np.float32)

    @classmethod
    def transform_hash_deformation(
        cls, training_deformation: TrainingDeformation
    ) -> str:
        """SHA-256 of sorted deformation transformations and source of apply"""
        payload = {
            "op_version": STORAGE_OP_VERSION,
            "patch_px": training_deformation.patch_px,
            "wrap_rad": str(training_deformation.wrap_rad),
            "normalize": training_deformation.normalize.value,
            "coherence_min": str(training_deformation.coherence_min),
        }
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
        return hashlib.sha256(blob).hexdigest()

    @classmethod
    def transform_hash_seismic(cls, training_seismic: TrainingSeismic) -> str:
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
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
        return hashlib.sha256(blob).hexdigest()

    @staticmethod
    def map_rejection_to_reason(rejection: str) -> InferenceAbstainReason:
        match rejection:
            case "coherence below min":
                return InferenceAbstainReason.LOW_COHERENCE
            case "snr below min":
                return InferenceAbstainReason.LOW_SNR
            case _:
                return InferenceAbstainReason.TRANSFORM_REJECTED
