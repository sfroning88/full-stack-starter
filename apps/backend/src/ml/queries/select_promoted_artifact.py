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
        mlflow_run_id,
        hf_repo_id,
        hf_revision,
        session_id::text,
        parent_id::text
    FROM {table}
    WHERE tier = %s::{tier_enum}
        AND role = %s::{role_enum}
        AND promoted = true
    ORDER BY promoted_at DESC
    LIMIT 1
""").format(
    table=sql.Identifier(*MODEL_ARTIFACT_TABLE),
    tier_enum=sql.Identifier(*MODEL_TIER_ENUM),
    role_enum=sql.Identifier(*MODEL_ROLE_ENUM),
    stage_enum=sql.Identifier(*TRAINING_STAGE_ENUM),
    precision_enum=sql.Identifier(*TRAINING_PRECISION_ENUM),
)
