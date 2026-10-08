"""
Author: Sean Froning
Created Date: 10.7.2026
Unit tests for backend PersistService
"""

from unittest.mock import patch

from my_python import MyClass, PoolFetch
from integrations.backend.services.persist_service import PersistService


def test_select_last_message_maps_row():
    row = {"id": "msg-1", "message": "hello"}
    with patch(
        "integrations.backend.services.persist_service.db_pool.run",
        return_value=row,
    ) as run:
        result = PersistService.select_last_message()
    run.assert_called_once()
    assert run.call_args.args[1] == ()
    assert run.call_args.kwargs["fetch"] is PoolFetch.ONE
    assert run.call_args.kwargs["error_event"] == "fetch_last_message_failed"
    assert isinstance(result, MyClass)
    assert result.id == "msg-1"
    assert result.message == "hello"


def test_select_last_message_returns_none_when_empty():
    with patch(
        "integrations.backend.services.persist_service.db_pool.run",
        return_value=None,
    ) as run:
        result = PersistService.select_last_message()
    run.assert_called_once()
    assert result is None
