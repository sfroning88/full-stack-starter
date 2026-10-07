from psycopg2 import sql
from fiery_python import (
    TRAINING_HYPERPARAMETER_QUANTIZE_TABLE,
    TRAINING_QUANTIZE_METHOD_ENUM,
    TRAINING_PRECISION_ENUM,
)

QUERY = sql.SQL("""
    SELECT id::text,
        method::{method_enum},
        precision::{precision_enum},
        calibration_samples,
        accuracy_drop_threshold,
        qat_epochs,
        qat_learning_rate
    FROM {table}
    WHERE id = %s::uuid
    ORDER BY created_at DESC
    LIMIT 1
""").format(
    table=sql.Identifier(*TRAINING_HYPERPARAMETER_QUANTIZE_TABLE),
    method_enum=sql.Identifier(*TRAINING_QUANTIZE_METHOD_ENUM),
    precision_enum=sql.Identifier(*TRAINING_PRECISION_ENUM),
)
