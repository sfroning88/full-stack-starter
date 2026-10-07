from psycopg2 import sql
from fiery_python import (
    DATASET_VERSION_TABLE,
    TRAINING_STATUS_ENUM,
)

QUERY = sql.SQL("""
    SELECT id::text,
        transform_hash,
        manifest_path,
        shard_count,
        sample_count,
        status::{status_enum},
        contract_id::text
    FROM {table}
    WHERE id = %s::uuid
""").format(
    table=sql.Identifier(*DATASET_VERSION_TABLE),
    status_enum=sql.Identifier(*TRAINING_STATUS_ENUM),
)
