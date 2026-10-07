"""
Author: Sean Froning
Created Date: 8.17.2026
Process-local sync lazy singleton resource loader
"""

import threading
from typing import Callable, Optional, cast


class SyncLazyResource[T]:
    """Thread-safe, run-once lazy singleton for sync resources"""

    def __init__(self, factory: Callable[[], T]) -> None:
        self._factory = factory
        self._value: Optional[T] = None
        self._is_set = False
        self._lock = threading.Lock()

    @property
    def is_set(self) -> bool:
        """Whether the resource has been resolved"""
        return self._is_set

    def get(self) -> T:
        """Resolve the resource, building it once on first access"""
        if not self._is_set:
            with self._lock:
                if not self._is_set:
                    self._value = self._factory()
                    self._is_set = True
        return cast(T, self._value)

    def pop(self) -> Optional[T]:
        """Atomically clear and return the resource for teardown"""
        with self._lock:
            if not self._is_set:
                return None
            value = self._value
            self._value = None
            self._is_set = False
            return value

    def reset(self) -> None:
        """Drop the cached resource so the next access rebuilds it"""
        with self._lock:
            self._value = None
            self._is_set = False
