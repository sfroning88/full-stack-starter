from psycopg2 import sql
from fiery_python import (
    TRAINING_SESSION_TABLE,
    TRAINING_SIGNAL_ENUM,
    TRAINING_STAGE_ENUM,
    TRAINING_STATUS_ENUM,
)

QUERY = sql.SQL("""
    INSERT INTO {table}
    (
        id,
        signal,
        stage,
        status,
        samples,
        seed,
        git_sha,
        git_url,
        started_at,
        finished_at,
        error_message,
        hyperparameter_pretrain_id,
        hyperparameter_lora_id,
        hyperparameter_distill_id,
        hyperparameter_prune_id,
        hyperparameter_quantize_id,
        contract_id,
        version_id,
        created_at,
        updated_at
    )
    VALUES (
        %(id)s::uuid,
        %(signal)s::{signal_enum},
        %(stage)s::{stage_enum},
        %(status)s::{status_enum},
        %(samples)s,
        %(seed)s,
        %(git_sha)s,
        %(git_url)s,
        %(started_at)s,
        %(finished_at)s,
        %(error_message)s,
        %(hyperparameter_pretrain_id)s::uuid,
        %(hyperparameter_lora_id)s::uuid,
        %(hyperparameter_distill_id)s::uuid,
        %(hyperparameter_prune_id)s::uuid,
        %(hyperparameter_quantize_id)s::uuid,
        %(contract_id)s::uuid,
        %(version_id)s::uuid,
        NOW(),
        NOW()
    )
    ON CONFLICT (id)
    DO UPDATE SET
        signal = EXCLUDED.signal,
        stage = EXCLUDED.stage,
        status = EXCLUDED.status,
        samples = EXCLUDED.samples,
        seed = EXCLUDED.seed,
        git_sha = EXCLUDED.git_sha,
        git_url = EXCLUDED.git_url,
        started_at = COALESCE(EXCLUDED.started_at, {table}.started_at),
        finished_at = COALESCE(EXCLUDED.finished_at, {table}.finished_at),
        error_message = COALESCE(EXCLUDED.error_message, {table}.error_message),
        hyperparameter_pretrain_id = EXCLUDED.hyperparameter_pretrain_id,
        hyperparameter_lora_id = EXCLUDED.hyperparameter_lora_id,
        hyperparameter_distill_id = EXCLUDED.hyperparameter_distill_id,
        hyperparameter_prune_id = EXCLUDED.hyperparameter_prune_id,
        hyperparameter_quantize_id = EXCLUDED.hyperparameter_quantize_id,
        contract_id = EXCLUDED.contract_id,
        version_id = EXCLUDED.version_id,
        updated_at = NOW()
""").format(
    table=sql.Identifier(*TRAINING_SESSION_TABLE),
    signal_enum=sql.Identifier(*TRAINING_SIGNAL_ENUM),
    stage_enum=sql.Identifier(*TRAINING_STAGE_ENUM),
    status_enum=sql.Identifier(*TRAINING_STATUS_ENUM),
)
