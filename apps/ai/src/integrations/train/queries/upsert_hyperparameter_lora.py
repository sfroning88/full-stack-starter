from psycopg2 import sql
from fiery_python import TRAINING_HYPERPARAMETER_LORA_TABLE

QUERY = sql.SQL("""
    INSERT INTO {table}
    (
        id,
        rank,
        alpha,
        dropout,
        epochs,
        learning_rate,
        target_modules_id,
        created_at,
        updated_at
    )
    VALUES (
        %(id)s::uuid,
        %(rank)s,
        %(alpha)s,
        %(dropout)s,
        %(epochs)s,
        %(learning_rate)s,
        %(target_modules_id)s::uuid,
        NOW(),
        NOW()
    )
    ON CONFLICT (id)
    DO UPDATE SET
        rank = EXCLUDED.rank,
        alpha = EXCLUDED.alpha,
        dropout = EXCLUDED.dropout,
        epochs = EXCLUDED.epochs,
        learning_rate = EXCLUDED.learning_rate,
        target_modules_id = EXCLUDED.target_modules_id,
        updated_at = NOW()
""").format(table=sql.Identifier(*TRAINING_HYPERPARAMETER_LORA_TABLE))
