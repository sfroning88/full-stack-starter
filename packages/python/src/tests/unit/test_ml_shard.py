"""
Author: Sean Froning
Created Date: 8.20.2026
Unit tests for Shard WebDataset tar pack/unpack
"""

import json

import numpy as np
import pytest
from fiery_python import Shard


def test_write_rejects_empty_key():
    phase = np.zeros((2, 2), dtype=np.float32)
    with pytest.raises(ValueError, match="sample key"):
        Shard.write([("", phase, {"label": "positive"})])


def test_write_rejects_duplicate_keys():
    phase = np.zeros((2, 2), dtype=np.float32)
    with pytest.raises(ValueError, match="duplicate sample key"):
        Shard.write(
            [
                ("a", phase, {"label": "positive"}),
                ("a", phase, {"label": "negative"}),
            ]
        )


def test_write_read_roundtrip_sorts_by_key():
    a = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    b = np.array([[5.0, 6.0], [7.0, 8.0]], dtype=np.float32)
    samples = [
        ("b", b, {"label": "negative", "split": "train"}),
        ("a", a, {"label": "positive", "split": "train"}),
    ]

    restored = Shard.read(Shard.write(samples))

    assert [key for key, _, _ in restored] == ["a", "b"]
    np.testing.assert_array_equal(restored[0][1], a)
    np.testing.assert_array_equal(restored[1][1], b)
    assert restored[0][2] == {"label": "positive", "split": "train"}
    assert restored[1][2] == {"label": "negative", "split": "train"}


def test_write_bytes_are_independent_of_caller_order():
    a = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    b = np.array([[5.0, 6.0], [7.0, 8.0]], dtype=np.float32)
    first = [
        ("b", b, {"label": "negative", "split": "train"}),
        ("a", a, {"label": "positive", "split": "train"}),
    ]
    second = [
        ("a", a, {"label": "positive", "split": "train"}),
        ("b", b, {"label": "negative", "split": "train"}),
    ]
    assert Shard.write(first) == Shard.write(second)


def test_write_read_roundtrip_preserves_keys_with_periods():
    phase = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    label = {"label": "positive", "split": "train"}
    restored = Shard.read(Shard.write([("tile.01", phase, label)]))
    assert restored[0][0] == "tile.01"
    np.testing.assert_array_equal(restored[0][1], phase)
    assert restored[0][2] == label


def test_write_manifest_is_canonical_json_bytes():
    body = Shard.write_manifest({"sample_count": 2, "shard_count": 1})
    assert json.loads(body) == {"sample_count": 2, "shard_count": 1}
    assert body == b'{"sample_count":2,"shard_count":1}'
