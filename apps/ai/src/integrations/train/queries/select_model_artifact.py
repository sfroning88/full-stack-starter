from psycopg2 import sql
from fiery_python import (
    MODEL_ARTIFACT_TABLE,
    MODEL_TIER_ENUM,
    MODEL_ROLE_ENUM,
    TRAINING_STAGE_ENUM,
    TRAINING_PRECISION_ENUM,
)

QUERY = sql.SQL("""
    SELECT id::text,
        tier::{tier_enum},
        role::{role_enum},
        stage::{stage_enum},
        precision::{precision_enum},
        architecture,
        param_count,
        sparsity,
        storage_path,
        signature,
        signed_at,
        promoted,
        promoted_at,
        session_id::text,
        parent_id::text
    FROM {table}
    WHERE id = %s::uuid
""").format(
    table=sql.Identifier(*MODEL_ARTIFACT_TABLE),
    tier_enum=sql.Identifier(*MODEL_TIER_ENUM),
    role_enum=sql.Identifier(*MODEL_ROLE_ENUM),
    stage_enum=sql.Identifier(*TRAINING_STAGE_ENUM),
    precision_enum=sql.Identifier(*TRAINING_PRECISION_ENUM),
)
