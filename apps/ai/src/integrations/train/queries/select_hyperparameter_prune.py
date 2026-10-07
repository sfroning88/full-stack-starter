from psycopg2 import sql
from fiery_python import (
    TRAINING_HYPERPARAMETER_PRUNE_TABLE,
    TRAINING_SPARSITY_SCHEDULE_ENUM,
    TRAINING_PRUNING_CRITERION_ENUM,
)

QUERY = sql.SQL("""
    SELECT id::text,
        target_sparsity,
        iterations,
        sparsity_schedule::{sparsity_schedule_enum},
        finetune_epochs_per_iter,
        pruning_criterion::{pruning_criterion_enum}
    FROM {table}
    WHERE id = %s::uuid
    ORDER BY created_at DESC
    LIMIT 1
""").format(
    table=sql.Identifier(*TRAINING_HYPERPARAMETER_PRUNE_TABLE),
    sparsity_schedule_enum=sql.Identifier(*TRAINING_SPARSITY_SCHEDULE_ENUM),
    pruning_criterion_enum=sql.Identifier(*TRAINING_PRUNING_CRITERION_ENUM),
)
