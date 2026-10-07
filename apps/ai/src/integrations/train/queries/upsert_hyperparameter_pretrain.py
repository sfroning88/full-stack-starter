from psycopg2 import sql
from fiery_python import (
    TRAINING_HYPERPARAMETER_PRETRAIN_TABLE,
    TRAINING_OPTIMIZER_ENUM,
    TRAINING_RATE_SCHEDULE_ENUM,
)

QUERY = sql.SQL("""
    INSERT INTO {table}
    (
        id,
        epochs,
        batch_size,
        learning_rate,
        optimizer,
        weight_decay,
        lr_schedule,
        seed,
        created_at,
        updated_at
    )
    VALUES (
        %(id)s::uuid,
        %(epochs)s,
        %(batch_size)s,
        %(learning_rate)s,
        %(optimizer)s::{optimizer_enum},
        %(weight_decay)s,
        %(lr_schedule)s::{lr_schedule_enum},
        %(seed)s,
        NOW(),
        NOW()
    )
    ON CONFLICT (id)
    DO UPDATE SET
        epochs = EXCLUDED.epochs,
        batch_size = EXCLUDED.batch_size,
        learning_rate = EXCLUDED.learning_rate,
        optimizer = EXCLUDED.optimizer,
        weight_decay = EXCLUDED.weight_decay,
        lr_schedule = EXCLUDED.lr_schedule,
        seed = EXCLUDED.seed,
        updated_at = NOW()
""").format(
    table=sql.Identifier(*TRAINING_HYPERPARAMETER_PRETRAIN_TABLE),
    optimizer_enum=sql.Identifier(*TRAINING_OPTIMIZER_ENUM),
    lr_schedule_enum=sql.Identifier(*TRAINING_RATE_SCHEDULE_ENUM),
)
