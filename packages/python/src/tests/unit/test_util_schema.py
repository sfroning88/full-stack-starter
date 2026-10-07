"""
Author: Sean Froning
Created Date: 8.17.2026
Unit tests for SchemaUtils field validators
"""

import pytest
from fiery_python.utils.schema import SchemaUtils


def test_non_empty_string_trims():
    assert SchemaUtils.non_empty_string("  hi  ") == "hi"


@pytest.mark.parametrize("value", [None, "", "   ", 5])
def test_non_empty_string_rejects(value):
    with pytest.raises(ValueError):
        SchemaUtils.non_empty_string(value)


def test_valid_email_accepts_and_trims():
    assert SchemaUtils.valid_email(" a@b.com ") == "a@b.com"


@pytest.mark.parametrize("value", ["no-at", "a@b", "a b@c.com", None])
def test_valid_email_rejects(value):
    with pytest.raises(ValueError):
        SchemaUtils.valid_email(value)


def test_valid_uuid_accepts():
    value = "8c9b8f3e-4d2a-5f1b-9e7c-2a1d6b4f0e35"
    assert SchemaUtils.valid_uuid(value) == value


@pytest.mark.parametrize("value", ["not-a-uuid", None, 123])
def test_valid_uuid_rejects(value):
    with pytest.raises(ValueError):
        SchemaUtils.valid_uuid(value)


def test_positive_int_accepts():
    assert SchemaUtils.positive_int(5) == 5


@pytest.mark.parametrize("value", [0, -1, None, True, "5"])
def test_positive_int_rejects(value):
    with pytest.raises(ValueError):
        SchemaUtils.positive_int(value)
