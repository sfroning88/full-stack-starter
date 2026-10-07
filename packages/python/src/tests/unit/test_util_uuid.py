"""
Author: Sean Froning
Created Date: 8.17.2026
Unit tests for UuidUtils deterministic generation
"""

import uuid
import pytest
from fiery_python import UuidUtils


def test_deterministic_uuid_is_stable():
    first = UuidUtils.deterministic_uuid("box_9", 3)
    second = UuidUtils.deterministic_uuid("box_9", 3)
    assert first == second


def test_deterministic_uuid_is_order_sensitive():
    assert UuidUtils.deterministic_uuid("a", "b") != UuidUtils.deterministic_uuid(
        "b", "a"
    )


def test_deterministic_uuid_is_type_sensitive():
    assert UuidUtils.deterministic_uuid("3") != UuidUtils.deterministic_uuid(3)


def test_deterministic_uuid_is_valid_uuid():
    value = UuidUtils.deterministic_uuid("box_9")
    assert uuid.UUID(value).version == 5


def test_deterministic_uuid_requires_fields():
    with pytest.raises(ValueError):
        UuidUtils.deterministic_uuid()
