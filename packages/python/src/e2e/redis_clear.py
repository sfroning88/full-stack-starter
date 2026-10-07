"""
Author: Sean Froning
Created Date: 8.21.2026
Shared redis cleanup for tests
"""

from ..fiery_python import queue


def clear_redis_queue() -> None:
    """Flush the RQ queue for this worker domain"""
    print("Clearing Redis queue")
    try:
        cleared = queue.clear()
        print(
            f"Redis queue cleared (queued={cleared['queued']}, failed={cleared['failed']})"
        )
    except Exception as err:
        print(f"Error clearing Redis queue: {str(err)}")
