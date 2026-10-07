from psycopg2 import sql
from fiery_python import (
    MODEL_ARTIFACT_TABLE,
    MODEL_TIER_ENUM,
    MODEL_ROLE_ENUM,
    TRAINING_STAGE_ENUM,
    TRAINING_PRECISION_ENUM,
)

QUERY = sql.SQL("""
    INSERT INTO {table}
    (
        id,
        tier,
        role,
        stage,
        precision,
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
        session_id,
        parent_id,
        created_at,
        updated_at
    )
    VALUES (
        %(id)s::uuid,
        %(tier)s::{tier_enum},
        %(role)s::{role_enum},
        %(stage)s::{stage_enum},
        %(precision)s::{precision_enum},
        %(architecture)s,
        %(param_count)s,
        %(sparsity)s,
        %(storage_path)s,
        %(signature)s,
        %(signed_at)s,
        %(promoted)s,
        %(promoted_at)s,
        %(mlflow_run_id)s,
        %(hf_repo_id)s,
        %(hf_revision)s,
        %(session_id)s::uuid,
        %(parent_id)s::uuid,
        NOW(),
        NOW()
    )
    ON CONFLICT (id)
    DO UPDATE SET
        tier = EXCLUDED.tier,
        role = EXCLUDED.role,
        stage = EXCLUDED.stage,
        precision = EXCLUDED.precision,
        architecture = EXCLUDED.architecture,
        param_count = EXCLUDED.param_count,
        sparsity = EXCLUDED.sparsity,
        storage_path = EXCLUDED.storage_path,
        signature = EXCLUDED.signature,
        signed_at = COALESCE(EXCLUDED.signed_at, {table}.signed_at),
        promoted = EXCLUDED.promoted,
        promoted_at = COALESCE(EXCLUDED.promoted_at, {table}.promoted_at),
        mlflow_run_id = EXCLUDED.mlflow_run_id,
        hf_repo_id = EXCLUDED.hf_repo_id,
        hf_revision = EXCLUDED.hf_revision,
        session_id = EXCLUDED.session_id,
        parent_id = EXCLUDED.parent_id,
        updated_at = NOW()
""").format(
    table=sql.Identifier(*MODEL_ARTIFACT_TABLE),
    tier_enum=sql.Identifier(*MODEL_TIER_ENUM),
    role_enum=sql.Identifier(*MODEL_ROLE_ENUM),
    stage_enum=sql.Identifier(*TRAINING_STAGE_ENUM),
    precision_enum=sql.Identifier(*TRAINING_PRECISION_ENUM),
)
