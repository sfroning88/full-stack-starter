"""
Author: Sean Froning
Created Date: 8.17.2026
Unit tests for database query placeholder normalization
"""

from fiery_python.core.db import _normalize_query


def test_normalize_query_rewrites_numbered_placeholders():
    sql = "SELECT * FROM t WHERE id = $1 AND batch = $2"
    assert _normalize_query(sql) == "SELECT * FROM t WHERE id = %s AND batch = %s"


def test_normalize_query_leaves_percent_placeholders_unchanged():
    sql = "SELECT * FROM t WHERE id = %s"
    assert _normalize_query(sql) == sql


def test_normalize_query_is_cached_for_identical_input():
    sql = "SELECT 1 WHERE id = $1"
    first = _normalize_query(sql)
    second = _normalize_query(sql)
    assert first is second
