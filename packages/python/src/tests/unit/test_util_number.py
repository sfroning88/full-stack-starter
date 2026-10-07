"""
Author: Sean Froning
Created Date: 8.17.2026
Unit tests for NumberUtils decimal clamping
"""

import math
from datetime import date

import pytest
from fiery_python import NumberUtils


def test_clamp_decimal_rounds_to_scale():
    assert NumberUtils.clamp_decimal(1.23456, precision=6, scale=4) == 1.2346


def test_clamp_decimal_clamps_above_limit():
    assert NumberUtils.clamp_decimal(999999.0, precision=6, scale=4) == 99.9999


def test_clamp_decimal_clamps_below_limit():
    assert NumberUtils.clamp_decimal(-999999.0, precision=6, scale=4) == -99.9999


def test_clamp_decimal_positive_infinity_maps_to_upper_limit():
    assert NumberUtils.clamp_decimal(math.inf, precision=6, scale=4) == 99.9999


def test_clamp_decimal_negative_infinity_maps_to_lower_limit():
    assert NumberUtils.clamp_decimal(-math.inf, precision=6, scale=4) == -99.9999


@pytest.mark.parametrize("value", [None, float("nan")])
def test_clamp_decimal_rejects_nan_or_none(value):
    with pytest.raises(ValueError):
        NumberUtils.clamp_decimal(value, precision=6, scale=4)


def test_encode_cyclical_uses_snapshot_month():
    sin_val, cos_val = NumberUtils.encode_cyclical(date(2024, 6, 1).toordinal())
    assert sin_val == pytest.approx(0.0)
    assert cos_val == pytest.approx(-1.0)


def test_encode_cyclical_january():
    sin_val, cos_val = NumberUtils.encode_cyclical(date(2024, 1, 15).toordinal())
    assert sin_val == pytest.approx(0.5)
    assert cos_val == pytest.approx(math.sqrt(3) / 2)


@pytest.mark.parametrize("value", [None, float("nan")])
def test_encode_cyclical_rejects_nan_or_none(value):
    with pytest.raises(ValueError):
        NumberUtils.encode_cyclical(value)
