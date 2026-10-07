from psycopg2 import sql
from fiery_python import (
    MODEL_METRIC_TABLE,
    MODEL_METRIC_NAME_ENUM,
    TRAINING_SPLIT_ENUM,
)

QUERY = sql.SQL("""
    INSERT INTO {table}
    (
        name,
        split,
        value,
        artifact_id,
        created_at,
        updated_at
    )
    VALUES %s
    ON CONFLICT (artifact_id, split, name)
    DO UPDATE SET
        value = EXCLUDED.value,
        updated_at = NOW()
""").format(table=sql.Identifier(*MODEL_METRIC_TABLE))

TEMPLATE = sql.SQL("""
    (
        %(name)s::{name_enum},
        %(split)s::{split_enum},
        %(value)s,
        %(artifact_id)s::uuid,
        NOW(),
        NOW()
    )
""").format(
    name_enum=sql.Identifier(*MODEL_METRIC_NAME_ENUM),
    split_enum=sql.Identifier(*TRAINING_SPLIT_ENUM),
)
