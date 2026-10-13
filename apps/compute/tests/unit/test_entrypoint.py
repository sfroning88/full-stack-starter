"""
Author: Sean Froning
Created Date: 10.7.2026
Unit tests for compute entrypoint
"""

from src.entrypoint import entrypoint


def test_entrypoint_returns_ok():
    assert entrypoint({}) == {"ok": True}
