"""
Author: Sean Froning
Created Date: 10.7.2026
Unit tests for backend PersistService
"""

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from my_python import MyClass, PoolFetch
from integrations.backend.services.persist_service import PersistService


def _session_returning(row):
    session = MagicMock()
    session.execute.return_value.mappings.return_value.first.return_value = row

    @contextmanager
    def get_session():
        yield session

    return get_session, session


def test_select_last_message_using_db_pool_maps_row():
    row = {"id": "msg-1", "message": "hello"}
    with patch(
        "integrations.backend.services.persist_service.db_pool.run",
        return_value=row,
    ) as run:
        result = PersistService.select_last_message_using_db_pool()
    run.assert_called_once()
    assert run.call_args.args[1] == ()
    assert run.call_args.kwargs["fetch"] is PoolFetch.ONE
    assert run.call_args.kwargs["error_event"] == "fetch_last_message_failed"
    assert isinstance(result, MyClass)
    assert result.id == "msg-1"
    assert result.message == "hello"


def test_select_last_message_using_db_pool_returns_none_when_empty():
    with patch(
        "integrations.backend.services.persist_service.db_pool.run",
        return_value=None,
    ) as run:
        result = PersistService.select_last_message_using_db_pool()
    run.assert_called_once()
    assert result is None


def test_select_last_message_using_sql_alchemy_maps_row():
    row = {"id": "msg-1", "message": "hello"}
    get_session, session = _session_returning(row)
    with patch(
        "integrations.backend.services.persist_service.sa.get_session",
        get_session,
    ):
        result = PersistService.select_last_message_using_sql_alchemy()
    session.execute.assert_called_once()
    assert isinstance(result, MyClass)
    assert result.id == "msg-1"
    assert result.message == "hello"


def test_select_last_message_using_sql_alchemy_returns_none_when_empty():
    get_session, session = _session_returning(None)
    with patch(
        "integrations.backend.services.persist_service.sa.get_session",
        get_session,
    ):
        result = PersistService.select_last_message_using_sql_alchemy()
    session.execute.assert_called_once()
    assert result is None
