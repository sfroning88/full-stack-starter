from psycopg2 import sql
from fiery_python import TRAINING_TARGET_MODULES_TABLE

QUERY = sql.SQL("""
    INSERT INTO {table}
    (
        id,
        query,
        key,
        value,
        output,
        created_at,
        updated_at
    )
    VALUES (
        %(id)s::uuid,
        %(query)s,
        %(key)s,
        %(value)s,
        %(output)s,
        NOW(),
        NOW()
    )
    ON CONFLICT (id)
    DO UPDATE SET
        query = EXCLUDED.query,
        key = EXCLUDED.key,
        value = EXCLUDED.value,
        output = EXCLUDED.output,
        updated_at = NOW()
""").format(table=sql.Identifier(*TRAINING_TARGET_MODULES_TABLE))
