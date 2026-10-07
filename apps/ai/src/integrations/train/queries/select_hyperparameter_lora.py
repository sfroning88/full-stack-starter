from psycopg2 import sql
from fiery_python import (
    TRAINING_HYPERPARAMETER_LORA_TABLE,
    TRAINING_TARGET_MODULES_TABLE,
)

QUERY = sql.SQL("""
    SELECT hyperparameter_lora.id::text,
        hyperparameter_lora.rank,
        hyperparameter_lora.alpha,
        hyperparameter_lora.dropout,
        hyperparameter_lora.epochs,
        hyperparameter_lora.learning_rate,
        hyperparameter_lora.target_modules_id::text,
        target_modules.query,
        target_modules.key,
        target_modules.value,
        target_modules.output
    FROM {hyperparameter_lora_table} hyperparameter_lora
    INNER JOIN {target_modules_table} target_modules
        ON hyperparameter_lora.target_modules_id = target_modules.id
    WHERE hyperparameter_lora.id = %s::uuid
    ORDER BY hyperparameter_lora.created_at DESC
    LIMIT 1
""").format(
    hyperparameter_lora_table=sql.Identifier(*TRAINING_HYPERPARAMETER_LORA_TABLE),
    target_modules_table=sql.Identifier(*TRAINING_TARGET_MODULES_TABLE),
)
