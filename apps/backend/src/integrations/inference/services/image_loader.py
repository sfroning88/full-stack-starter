"""
Author: Sean Froning
Created Date: 9.14.2026
Processing functions for Image loading
"""

import io
import numpy as np
from fastapi.responses import Response
from PIL import Image
from fiery_python import error
from fiery_python import BlobStorageServices
from ..schemas import InferencePreviewRequest
from .persist_service import InferencePersistService

_WAVEFORM_HEIGHT = 128
_WAVEFORM_MAX_WIDTH = 1024
_WAVEFORM_MARGIN = 4


class InferenceImageLoader:
    """Load and return the image"""

    @classmethod
    def run(cls, payload: InferencePreviewRequest) -> Response:
        interferogram_id = payload.interferogram_id
        seismic_event_id = payload.seismic_event_id
        interferogram = None
        seismic_event = None
        if interferogram_id:
            interferogram = InferencePersistService.select_interferogram(
                (interferogram_id, None)
            )
        elif seismic_event_id:
            seismic_event = InferencePersistService.select_seismic_event(
                (seismic_event_id, None)
            )
        else:
            raise error("No interferogram or seismic_event is selected")
        if interferogram:
            if not interferogram.id:
                interferogram.id = interferogram.deterministic_id()
            if not interferogram.id:
                raise error("Invalid interferogram_id")
            storage_path = interferogram.storage_path
            interferogram_id = interferogram.id
            seismic_event_id = None
        elif seismic_event:
            if not seismic_event.id:
                seismic_event.id = seismic_event.deterministic_id()
            if not seismic_event.id:
                raise error("Invalid seismic_event_id")
            storage_path = seismic_event.waveform_path
            seismic_event_id = seismic_event.id
            interferogram_id = None
        else:
            raise error("No image asset was found")
        body = BlobStorageServices.get_unrefined(storage_path)
        sample = InferencePersistService.load_npz(body)
        if interferogram_id:
            png = cls._interferogram_png_image(sample)
        else:
            png = cls._waveform_png_image(sample)
        return Response(
            content=png,
            status_code=200,
            media_type="image/png",
        )

    @classmethod
    def _interferogram_png_image(cls, sample: np.ndarray) -> bytes:
        plane = cls._phase_plane(sample)
        index = cls._values_to_uint8_index(plane)
        rgb = cls._hsv_to_rgb_uint8(index.astype(np.float32) / 255.0)
        return cls._png_bytes_from_rgb(rgb)

    @classmethod
    def _waveform_png_image(cls, sample: np.ndarray) -> bytes:
        trace = cls._waveform_trace(sample)
        width = min(int(trace.size), _WAVEFORM_MAX_WIDTH)
        if trace.size == 0:
            rgb = np.full((_WAVEFORM_HEIGHT, 1, 3), 255, dtype=np.uint8)
            return cls._png_bytes_from_rgb(rgb)
        trace = cls._resample_1d(trace, width)
        lo, hi = cls._value_range(trace)
        norm = cls._normalize_01(trace, lo, hi)
        if norm is None:
            ys = np.full(width, _WAVEFORM_HEIGHT // 2, dtype=np.int32)
        else:
            ys = cls._waveform_rows_from_norm(norm)
        rgb = cls._rasterize_trace_rows(ys, _WAVEFORM_HEIGHT)
        return cls._png_bytes_from_rgb(rgb)

    @staticmethod
    def _sample_as_float32(sample: np.ndarray) -> np.ndarray:
        return np.asarray(sample, dtype=np.float32)

    @staticmethod
    def _phase_plane(sample: np.ndarray) -> np.ndarray:
        array = InferenceImageLoader._sample_as_float32(sample)
        if array.ndim >= 2:
            return array[0]
        return array.reshape(1, -1)

    @staticmethod
    def _waveform_trace(sample: np.ndarray) -> np.ndarray:
        trace = np.squeeze(InferenceImageLoader._sample_as_float32(sample))
        if trace.ndim != 1:
            return trace.reshape(-1)
        return trace

    @staticmethod
    def _value_range(values: np.ndarray) -> tuple[float, float]:
        return float(np.nanmin(values)), float(np.nanmax(values))

    @staticmethod
    def _normalize_01(values: np.ndarray, lo: float, hi: float) -> np.ndarray | None:
        if hi <= lo:
            return None
        return (values - lo) / (hi - lo)

    @staticmethod
    def _values_to_uint8_index(values: np.ndarray) -> np.ndarray:
        lo, hi = InferenceImageLoader._value_range(values)
        norm = InferenceImageLoader._normalize_01(values, lo, hi)
        if norm is None:
            return np.zeros(values.shape, dtype=np.uint8)
        return (norm * 255.0).clip(0, 255).astype(np.uint8)

    @staticmethod
    def _resample_1d(trace: np.ndarray, width: int) -> np.ndarray:
        if trace.size == width:
            return trace
        x_src = np.linspace(0, trace.size - 1, width)
        return np.interp(x_src, np.arange(trace.size), trace).astype(np.float32)

    @staticmethod
    def _waveform_rows_from_norm(norm: np.ndarray) -> np.ndarray:
        span = _WAVEFORM_HEIGHT - 2 * _WAVEFORM_MARGIN
        ys = (_WAVEFORM_MARGIN + (1.0 - norm) * max(span - 1, 0)).round()
        ys = ys.astype(np.int32)
        return np.clip(ys, _WAVEFORM_MARGIN, _WAVEFORM_HEIGHT - _WAVEFORM_MARGIN - 1)

    @staticmethod
    def _rasterize_trace_rows(ys: np.ndarray, height: int) -> np.ndarray:
        width = ys.size
        xs = np.arange(width, dtype=np.int32)
        rgb = np.full((height, width, 3), 255, dtype=np.uint8)
        rgb[ys, xs] = (0, 0, 0)
        rgb[np.clip(ys - 1, 0, height - 1), xs] = (0, 0, 0)
        rgb[np.clip(ys + 1, 0, height - 1), xs] = (0, 0, 0)
        return rgb

    @staticmethod
    def _png_bytes_from_rgb(rgb: np.ndarray) -> bytes:
        if rgb.ndim != 3 or rgb.shape[-1] != 3:
            raise ValueError("expected RGB array with shape (H, W, 3)")
        buf = io.BytesIO()
        Image.fromarray(np.ascontiguousarray(rgb), mode="RGB").save(buf, format="PNG")
        return buf.getvalue()

    @staticmethod
    def _hsv_to_rgb_uint8(h01: np.ndarray) -> np.ndarray:
        h = (h01 % 1.0) * 6.0
        i = np.floor(h).astype(np.int32)
        f = h - i
        p = np.zeros_like(h01)
        q = 1.0 - f
        t = f
        r = np.choose(i % 6, [1, q, p, p, t, 1])
        g = np.choose(i % 6, [t, 1, 1, q, p, p])
        b = np.choose(i % 6, [p, p, t, 1, 1, q])
        rgb = np.stack([r, g, b], axis=-1)
        return (rgb * 255.0).clip(0, 255).astype(np.uint8)
