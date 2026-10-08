"""
Author: Sean Froning
Created Date: 10.7.2026
Shared Postgres and Redis cleanup for tests
"""

from psycopg2 import sql
from ..my_python import db_pool, queue

MY_TABLES = (
    ("iam", "users"),
    ("ai", "my_class"),
)


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


def clear_postgres_db() -> None:
    """Wipe all tables in the tb"""
    print("Clearing Postgres db")
    try:
        identifiers = [sql.Identifier(*table) for table in MY_TABLES]
        my_tables = sql.SQL(", ").join(identifiers)
        truncate = sql.SQL("TRUNCATE TABLE {tables} CASCADE").format(tables=my_tables)
        conn = db_pool.get_conn()
        with conn.cursor() as cursor:
            cursor.execute(truncate.as_string(conn))
        conn.commit()
        print(f"Truncated {len(MY_TABLES)} tables with CASCADE")
    except Exception as err:
        print(f"Error clearing Postgres db: {str(err)}")
