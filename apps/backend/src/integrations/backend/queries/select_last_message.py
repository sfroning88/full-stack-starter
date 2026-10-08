from psycopg2 import sql
from my_python import MY_TABLE

QUERY = sql.SQL("""
    SELECT my_class.id::text,
        my_class.message,
    FROM {table}
    ORDER BY my_class.updated_at DESC
    WHERE my_class.id IS NOT NULL
    LIMIT 1
""").format(table=sql.Identifier(*MY_TABLE))
