"""
Author: Sean Froning
Created Date: 9.14.2026
Unit tests for InferenceImageLoader
"""

import io
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch

import numpy as np
import pytest
from PIL import Image
from fiery_python import error
from fiery_python import (
    TrainingDeformationLabel,
    TrainingSampleSource,
    TrainingSeismicLabel,
    TrainingSplit,
    TrainingInterferogram,
    TrainingSeismicEvent,
)
from integrations.inference.schemas import InferencePreviewRequest
from integrations.inference.services.image_loader import InferenceImageLoader

IFG_ID = "22222222-2222-2222-2222-222222222222"
EVT_ID = "33333333-3333-3333-3333-333333333333"
VOL_ID = "44444444-4444-4444-4444-444444444444"
NOW = datetime.now(timezone.utc)
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _deformation_request() -> InferencePreviewRequest:
    return InferencePreviewRequest(interferogram_id=IFG_ID)


def _seismic_request() -> InferencePreviewRequest:
    return InferencePreviewRequest(seismic_event_id=EVT_ID)


def _interferogram() -> TrainingInterferogram:
    return TrainingInterferogram(
        id=IFG_ID,
        source=TrainingSampleSource.HEPHAESTUS,
        split=TrainingSplit.HOLDOUT,
        label=TrainingDeformationLabel.POSITIVE,
        storage_path="hephaestus/abc.npz",
        volcano_id=VOL_ID,
    )


def _seismic_event() -> TrainingSeismicEvent:
    return TrainingSeismicEvent(
        id=EVT_ID,
        source=TrainingSampleSource.LLAIMA,
        split=TrainingSplit.HOLDOUT,
        label=TrainingSeismicLabel.LP,
        recorded_at=NOW,
        duration_s=Decimal("60.000"),
        sampling_hz=100,
        waveform_path="llaima/abc.npz",
        volcano_id=VOL_ID,
    )


def test_interferogram_png_writes_png_header():
    sample = np.linspace(0, 1, 16, dtype=np.float32).reshape(2, 2, 4)
    png = InferenceImageLoader._interferogram_png_image(sample)
    assert png.startswith(PNG_MAGIC)


def test_waveform_png_writes_png_header():
    sample = np.linspace(-1, 1, 8, dtype=np.float32)
    png = InferenceImageLoader._waveform_png_image(sample)
    assert png.startswith(PNG_MAGIC)


def test_interferogram_png_decodes_as_rgb_with_distinct_channels():
    sample = np.linspace(0, 1, 4, dtype=np.float32).reshape(1, 2, 2)
    png = InferenceImageLoader._interferogram_png_image(sample)
    with Image.open(io.BytesIO(png)) as img:
        assert img.mode == "RGB"
    arr = np.asarray(Image.open(io.BytesIO(png)))
    assert not np.allclose(arr[..., 0], arr[..., 1])


def test_phase_plane_uses_first_channel():
    sample = np.stack(
        [
            np.full((2, 2), 3.0, dtype=np.float32),
            np.full((2, 2), 9.0, dtype=np.float32),
        ]
    )
    phase = InferenceImageLoader._phase_plane(sample)
    assert phase.shape == (2, 2)
    assert phase.dtype == np.float32
    assert np.all(phase == 3.0)


def test_phase_plane_flattens_1d_waveform():
    sample = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    phase = InferenceImageLoader._phase_plane(sample)
    assert phase.shape == (1, 3)
    np.testing.assert_allclose(phase, sample.reshape(1, -1))


def test_waveform_trace_squeezes_to_1d():
    sample = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    trace = InferenceImageLoader._waveform_trace(sample)
    assert trace.shape == (3,)
    np.testing.assert_allclose(trace, sample)


def test_waveform_png_renders_taller_than_strip():
    sample = np.array([0.0, 1.0, 0.0, -1.0], dtype=np.float32)
    png = InferenceImageLoader._waveform_png_image(sample)
    with Image.open(io.BytesIO(png)) as img:
        assert img.mode == "RGB"
        assert img.size[1] > 1


def test_values_to_uint8_index_scales_min_max():
    phase = np.array([[0.0, 0.5, 1.0]], dtype=np.float32)
    index = InferenceImageLoader._values_to_uint8_index(phase)
    assert index.dtype == np.uint8
    np.testing.assert_array_equal(index, [[0, 127, 255]])


def test_values_to_uint8_index_constant_values_is_zero():
    phase = np.full((2, 2), 5.0, dtype=np.float32)
    index = InferenceImageLoader._values_to_uint8_index(phase)
    assert np.all(index == 0)


def test_normalize_01_returns_none_when_range_degenerate():
    values = np.array([2.0, 2.0], dtype=np.float32)
    lo, hi = InferenceImageLoader._value_range(values)
    assert InferenceImageLoader._normalize_01(values, lo, hi) is None


def test_hsv_to_rgb_uint8_varies_by_hue():
    h = np.array([[0.0, 0.5]], dtype=np.float32)
    rgb = InferenceImageLoader._hsv_to_rgb_uint8(h)
    assert rgb.shape == (1, 2, 3)
    assert rgb.dtype == np.uint8
    assert not np.array_equal(rgb[0, 0], rgb[0, 1])


def test_png_bytes_from_rgb_writes_decodable_rgb():
    rgb = np.zeros((2, 2, 3), dtype=np.uint8)
    rgb[0, 0] = (255, 0, 0)
    png = InferenceImageLoader._png_bytes_from_rgb(rgb)
    assert png.startswith(PNG_MAGIC)
    with Image.open(io.BytesIO(png)) as img:
        assert img.mode == "RGB"
        assert img.size == (2, 2)


def test_png_bytes_from_rgb_rejects_invalid_shape():
    with pytest.raises(ValueError, match="expected RGB"):
        InferenceImageLoader._png_bytes_from_rgb(np.zeros((2, 2), dtype=np.uint8))


def test_run_raises_when_sample_unselected():
    payload = InferencePreviewRequest()
    with pytest.raises(error, match="interferogram or seismic_event"):
        InferenceImageLoader.run(payload)


def test_run_raises_when_interferogram_missing():
    with patch(
        "integrations.inference.services.image_loader.InferencePersistService.select_interferogram",
        return_value=None,
    ):
        with pytest.raises(error, match="No image asset"):
            InferenceImageLoader.run(_deformation_request())


def test_run_raises_when_seismic_event_missing():
    with patch(
        "integrations.inference.services.image_loader.InferencePersistService.select_seismic_event",
        return_value=None,
    ):
        with pytest.raises(error, match="No image asset"):
            InferenceImageLoader.run(_seismic_request())


def test_run_returns_png_for_interferogram():
    sample = np.zeros((2, 4, 4), dtype=np.float32)
    sample[0, 0, 0] = 1.0
    with (
        patch(
            "integrations.inference.services.image_loader.InferencePersistService.select_interferogram",
            return_value=_interferogram(),
        ) as select_interferogram,
        patch(
            "integrations.inference.services.image_loader.BlobStorageServices.get_unrefined",
            return_value=b"npz",
        ) as get_unrefined,
        patch(
            "integrations.inference.services.image_loader.InferencePersistService.load_npz",
            return_value=sample,
        ) as load_npz,
    ):
        response = InferenceImageLoader.run(_deformation_request())
    select_interferogram.assert_called_once_with((IFG_ID, None))
    get_unrefined.assert_called_once_with("hephaestus/abc.npz")
    load_npz.assert_called_once_with(b"npz")
    assert response.media_type == "image/png"
    assert response.status_code == 200
    assert response.body.startswith(PNG_MAGIC)


def test_run_returns_png_for_seismic_event():
    sample = np.zeros(16, dtype=np.float32)
    sample[0] = 1.0
    with (
        patch(
            "integrations.inference.services.image_loader.InferencePersistService.select_seismic_event",
            return_value=_seismic_event(),
        ) as select_event,
        patch(
            "integrations.inference.services.image_loader.BlobStorageServices.get_unrefined",
            return_value=b"npz",
        ) as get_unrefined,
        patch(
            "integrations.inference.services.image_loader.InferencePersistService.load_npz",
            return_value=sample,
        ),
    ):
        response = InferenceImageLoader.run(_seismic_request())
    select_event.assert_called_once_with((EVT_ID, None))
    get_unrefined.assert_called_once_with("llaima/abc.npz")
    assert response.media_type == "image/png"
    assert response.body.startswith(PNG_MAGIC)
    with Image.open(io.BytesIO(response.body)) as img:
        assert img.size[1] > 1
