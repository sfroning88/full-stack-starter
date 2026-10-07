"""
Author: Sean Froning
Created Date: 8.17.2026
Unit tests for SyncLazyResource lazy initialization
"""

from fiery_python import SyncLazyResource


def test_sync_lazy_builds_once():
    calls = 0

    def factory():
        nonlocal calls
        calls += 1
        return {"ready": True}

    resource = SyncLazyResource(factory)
    assert resource.is_set is False
    first = resource.get()
    second = resource.get()
    assert first is second
    assert calls == 1
    assert resource.is_set is True


def test_sync_lazy_pop_clears_cached_value():
    resource = SyncLazyResource(lambda: "value")
    assert resource.get() == "value"
    popped = resource.pop()
    assert popped == "value"
    assert resource.is_set is False


def test_sync_lazy_reset_rebuilds_on_next_access():
    counter = 0

    def factory():
        nonlocal counter
        counter += 1
        return counter

    resource = SyncLazyResource(factory)
    assert resource.get() == 1
    resource.reset()
    assert resource.is_set is False
    assert resource.get() == 2
