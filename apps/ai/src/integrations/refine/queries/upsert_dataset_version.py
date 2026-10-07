from psycopg2 import sql
from fiery_python import (
    DATASET_VERSION_TABLE,
    TRAINING_STATUS_ENUM,
)

QUERY = sql.SQL("""
    INSERT INTO {table}
    (
        id,
        transform_hash,
        manifest_path,
        shard_count,
        sample_count,
        status,
        contract_id,
        created_at,
        updated_at
    )
    VALUES (
        %(id)s::uuid,
        %(transform_hash)s,
        %(manifest_path)s,
        %(shard_count)s,
        %(sample_count)s,
        %(status)s::{status_enum},
        %(contract_id)s::uuid,
        NOW(),
        NOW()
    )
    ON CONFLICT (contract_id, transform_hash)
    DO UPDATE SET
        manifest_path = EXCLUDED.manifest_path,
        shard_count = EXCLUDED.shard_count,
        sample_count = EXCLUDED.sample_count,
        status = EXCLUDED.status,
        updated_at = NOW()
""").format(
    table=sql.Identifier(*DATASET_VERSION_TABLE),
    status_enum=sql.Identifier(*TRAINING_STATUS_ENUM),
)
