from psycopg2 import sql
from fiery_python import (
    TRAINING_SESSION_TABLE,
    TRAINING_SIGNAL_ENUM,
    TRAINING_STAGE_ENUM,
    TRAINING_STATUS_ENUM,
)

QUERY = sql.SQL("""
    SELECT id::text,
        signal::{signal_enum},
        stage::{stage_enum},
        status::{status_enum},
        samples,
        seed,
        git_sha,
        git_url,
        started_at,
        finished_at,
        error_message,
        hyperparameter_pretrain_id::text,
        hyperparameter_lora_id::text,
        hyperparameter_distill_id::text,
        hyperparameter_prune_id::text,
        hyperparameter_quantize_id::text,
        contract_id::text,
        version_id::text
    FROM {table}
    WHERE id = %s::uuid
""").format(
    table=sql.Identifier(*TRAINING_SESSION_TABLE),
    signal_enum=sql.Identifier(*TRAINING_SIGNAL_ENUM),
    stage_enum=sql.Identifier(*TRAINING_STAGE_ENUM),
    status_enum=sql.Identifier(*TRAINING_STATUS_ENUM),
)
