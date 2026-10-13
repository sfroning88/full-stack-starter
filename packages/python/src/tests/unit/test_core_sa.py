"""
Author: Sean Froning
Created Date: 10.7.2026
Unit tests for SQLAlchemy pool URL cleaning
"""

from my_python.core.sa import sa


def test_clean_pool_url_strips_pgbouncer_and_marks_pooled():
    url = "postgresql://u:p@host:5432/db?pgbouncer=true&sslmode=require"
    cleaned, pooled = sa._clean_pool_url(url)
    assert pooled is True
    assert cleaned == "postgresql://u:p@host:5432/db?sslmode=require"


def test_clean_pool_url_marks_pooler_port_pooled():
    url = "postgresql://u:p@host:6543/db"
    cleaned, pooled = sa._clean_pool_url(url)
    assert pooled is True
    assert cleaned == url


def test_clean_pool_url_leaves_direct_url_unpooled():
    url = "postgresql://u:p@host:5432/db"
    cleaned, pooled = sa._clean_pool_url(url)
    assert pooled is False
    assert cleaned == url
