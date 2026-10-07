"""
Author: Sean Froning
Created Date: 8.17.2026
Unit tests for AsyncLazyResource lazy initialization
"""

import asyncio
from fiery_python import AsyncLazyResource


def test_async_lazy_builds_once():
    calls = 0

    async def factory():
        nonlocal calls
        calls += 1
        return {"ready": True}

    resource = AsyncLazyResource(factory)

    async def run():
        assert resource.is_set is False
        first = await resource.get()
        second = await resource.get()
        assert first is second
        assert calls == 1
        assert resource.is_set is True

    asyncio.run(run())


def test_async_lazy_pop_clears_cached_value():
    resource = AsyncLazyResource(lambda: asyncio.sleep(0, result="value"))

    async def run():
        assert await resource.get() == "value"
        popped = await resource.pop()
        assert popped == "value"
        assert resource.is_set is False

    asyncio.run(run())


def test_async_lazy_reset_rebuilds_on_next_access():
    counter = 0

    async def factory():
        nonlocal counter
        counter += 1
        return counter

    resource = AsyncLazyResource(factory)

    async def run():
        assert await resource.get() == 1
        await resource.reset()
        assert resource.is_set is False
        assert await resource.get() == 2

    asyncio.run(run())
