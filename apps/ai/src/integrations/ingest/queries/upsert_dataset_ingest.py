from psycopg2 import sql
from fiery_python import (
    DATASET_INGEST_TABLE,
    TRAINING_SAMPLE_SOURCE_ENUM,
    TRAINING_STATUS_ENUM,
)

QUERY = sql.SQL("""
    INSERT INTO {table}
    (
        id,
        source,
        asset_count,
        status,
        started_at,
        finished_at,
        error_message,
        created_at,
        updated_at
    )
    VALUES (
        %(id)s::uuid,
        %(source)s::{source_enum},
        %(asset_count)s,
        %(status)s::{status_enum},
        %(started_at)s,
        %(finished_at)s,
        %(error_message)s,
        NOW(),
        NOW()
    )
    ON CONFLICT (id)
    DO UPDATE SET
        source = EXCLUDED.source,
        asset_count = EXCLUDED.asset_count,
        status = EXCLUDED.status,
        started_at = EXCLUDED.started_at,
        finished_at = EXCLUDED.finished_at,
        error_message = COALESCE(
            EXCLUDED.error_message, {table}.error_message
        ),
        updated_at = NOW()
""").format(
    table=sql.Identifier(*DATASET_INGEST_TABLE),
    source_enum=sql.Identifier(*TRAINING_SAMPLE_SOURCE_ENUM),
    status_enum=sql.Identifier(*TRAINING_STATUS_ENUM),
)
