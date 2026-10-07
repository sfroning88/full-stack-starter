from psycopg2 import sql
from fiery_python import (
    TRAINING_HYPERPARAMETER_PRUNE_TABLE,
    TRAINING_SPARSITY_SCHEDULE_ENUM,
    TRAINING_PRUNING_CRITERION_ENUM,
)

QUERY = sql.SQL("""
    INSERT INTO {table}
    (
        id,
        target_sparsity,
        iterations,
        sparsity_schedule,
        finetune_epochs_per_iter,
        pruning_criterion,
        created_at,
        updated_at
    )
    VALUES (
        %(id)s::uuid,
        %(target_sparsity)s,
        %(iterations)s,
        %(sparsity_schedule)s::{sparsity_schedule_enum},
        %(finetune_epochs_per_iter)s,
        %(pruning_criterion)s::{pruning_criterion_enum},
        NOW(),
        NOW()
    )
    ON CONFLICT (id)
    DO UPDATE SET
        target_sparsity = EXCLUDED.target_sparsity,
        iterations = EXCLUDED.iterations,
        sparsity_schedule = EXCLUDED.sparsity_schedule,
        finetune_epochs_per_iter = EXCLUDED.finetune_epochs_per_iter,
        pruning_criterion = EXCLUDED.pruning_criterion,
        updated_at = NOW()
""").format(
    table=sql.Identifier(*TRAINING_HYPERPARAMETER_PRUNE_TABLE),
    sparsity_schedule_enum=sql.Identifier(*TRAINING_SPARSITY_SCHEDULE_ENUM),
    pruning_criterion_enum=sql.Identifier(*TRAINING_PRUNING_CRITERION_ENUM),
)
