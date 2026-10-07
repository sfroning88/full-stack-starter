from psycopg2 import sql
from fiery_python import (
    TRAINING_HYPERPARAMETER_PRETRAIN_TABLE,
    TRAINING_OPTIMIZER_ENUM,
    TRAINING_RATE_SCHEDULE_ENUM,
)

QUERY = sql.SQL("""
    SELECT id::text,
        epochs,
        batch_size,
        learning_rate,
        optimizer::{optimizer_enum},
        weight_decay,
        lr_schedule::{lr_schedule_enum},
        seed
    FROM {table}
    WHERE id = %s::uuid
    ORDER BY created_at DESC
    LIMIT 1
""").format(
    table=sql.Identifier(*TRAINING_HYPERPARAMETER_PRETRAIN_TABLE),
    optimizer_enum=sql.Identifier(*TRAINING_OPTIMIZER_ENUM),
    lr_schedule_enum=sql.Identifier(*TRAINING_RATE_SCHEDULE_ENUM),
)
