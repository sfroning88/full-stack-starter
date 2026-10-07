from psycopg2 import sql
from fiery_python import (
    MODEL_ARTIFACT_TABLE,
    TRAINING_SESSION_TABLE,
    MODEL_TIER_ENUM,
    MODEL_ROLE_ENUM,
    TRAINING_STAGE_ENUM,
    TRAINING_STATUS_ENUM,
    TRAINING_PRECISION_ENUM,
)

QUERY = sql.SQL("""
    SELECT model_artifact.id::text,
        model_artifact.tier::{tier_enum},
        model_artifact.role::{role_enum},
        model_artifact.stage::{stage_enum},
        model_artifact.precision::{precision_enum},
        model_artifact.architecture,
        model_artifact.param_count,
        model_artifact.sparsity,
        model_artifact.storage_path,
        model_artifact.signature,
        model_artifact.signed_at,
        model_artifact.promoted,
        model_artifact.promoted_at,
        model_artifact.mlflow_run_id,
        model_artifact.hf_repo_id,
        model_artifact.hf_revision,
        model_artifact.session_id::text,
        model_artifact.parent_id::text
    FROM {artifact_table} model_artifact
    INNER JOIN {session_table} training_session
        ON model_artifact.session_id = training_session.id
    WHERE model_artifact.tier = %s::{tier_enum}
        AND model_artifact.role = %s::{role_enum}
        AND training_session.status = 'completed'::{status_enum}
        AND promoted = TRUE
    ORDER BY model_artifact.promoted_at DESC
    LIMIT 1
""").format(
    artifact_table=sql.Identifier(*MODEL_ARTIFACT_TABLE),
    session_table=sql.Identifier(*TRAINING_SESSION_TABLE),
    tier_enum=sql.Identifier(*MODEL_TIER_ENUM),
    role_enum=sql.Identifier(*MODEL_ROLE_ENUM),
    stage_enum=sql.Identifier(*TRAINING_STAGE_ENUM),
    status_enum=sql.Identifier(*TRAINING_STATUS_ENUM),
    precision_enum=sql.Identifier(*TRAINING_PRECISION_ENUM),
)
