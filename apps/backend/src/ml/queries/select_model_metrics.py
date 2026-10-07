from psycopg2 import sql
from fiery_python import (
    MODEL_METRIC_TABLE,
    MODEL_METRIC_NAME_ENUM,
    TRAINING_SPLIT_ENUM,
)

QUERY = sql.SQL("""
    SELECT name::{name_enum},
        split::{split_enum},
        value,
        artifact_id::text
    FROM {table}
    WHERE artifact_id = %s::uuid
""").format(
    table=sql.Identifier(*MODEL_METRIC_TABLE),
    name_enum=sql.Identifier(*MODEL_METRIC_NAME_ENUM),
    split_enum=sql.Identifier(*TRAINING_SPLIT_ENUM),
)
