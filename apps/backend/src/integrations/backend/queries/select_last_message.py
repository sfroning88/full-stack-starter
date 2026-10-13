from psycopg2 import sql
from sqlalchemy import text
from my_python import MY_TABLE

_schema, _name = MY_TABLE

QUERY_DB_POOL = sql.SQL("""
    SELECT my_class.id::text,
        my_class.message,
    FROM {table}
    WHERE my_class.id IS NOT NULL
    ORDER BY my_class.updated_at DESC
    LIMIT 1
""").format(table=sql.Identifier(*MY_TABLE))

QUERY_SQL_ALCHEMY = text(f"""
    SELECT my_class.id::text,
        my_class.message,
    FROM {_schema}.{_name}
    WHERE my_class.id IS NOT NULL
    ORDER BY my_class.updated_at DESC
    LIMIT 1
""")
