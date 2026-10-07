"""
Author: Sean Froning
Created Date: 8.17.2026
Process-local async lazy singleton resource loader
"""

import asyncio
from typing import Awaitable, Callable, Optional, cast


class AsyncLazyResource[T]:
    """Asyncio-safe, run-once lazy singleton for async resources"""

    def __init__(self, factory: Callable[[], Awaitable[T]]) -> None:
        self._factory = factory
        self._value: Optional[T] = None
        self._is_set = False
        self._lock = asyncio.Lock()

    @property
    def is_set(self) -> bool:
        """Whether the resource has been resolved"""
        return self._is_set

    async def get(self) -> T:
        """Resolve the resource, awaiting the factory once on first access"""
        if not self._is_set:
            async with self._lock:
                if not self._is_set:
                    self._value = await self._factory()
                    self._is_set = True
        return cast(T, self._value)

    async def pop(self) -> Optional[T]:
        """Atomically clear and return the resource for teardown"""
        async with self._lock:
            if not self._is_set:
                return None
            value = self._value
            self._value = None
            self._is_set = False
            return value

    async def reset(self) -> None:
        """Drop the cached resource so the next access rebuilds it"""
        async with self._lock:
            self._value = None
            self._is_set = False
