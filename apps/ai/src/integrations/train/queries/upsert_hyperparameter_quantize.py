from psycopg2 import sql
from fiery_python import (
    TRAINING_HYPERPARAMETER_QUANTIZE_TABLE,
    TRAINING_QUANTIZE_METHOD_ENUM,
    TRAINING_PRECISION_ENUM,
)

QUERY = sql.SQL("""
    INSERT INTO {table}
    (
        id,
        method,
        precision,
        calibration_samples,
        accuracy_drop_threshold,
        qat_epochs,
        qat_learning_rate,
        created_at,
        updated_at
    )
    VALUES (
        %(id)s::uuid,
        %(method)s::{method_enum},
        %(precision)s::{precision_enum},
        %(calibration_samples)s,
        %(accuracy_drop_threshold)s,
        %(qat_epochs)s,
        %(qat_learning_rate)s,
        NOW(),
        NOW()
    )
    ON CONFLICT (id)
    DO UPDATE SET
        method = EXCLUDED.method,
        precision = EXCLUDED.precision,
        calibration_samples = EXCLUDED.calibration_samples,
        accuracy_drop_threshold = EXCLUDED.accuracy_drop_threshold,
        qat_epochs = EXCLUDED.qat_epochs,
        qat_learning_rate = EXCLUDED.qat_learning_rate,
        updated_at = NOW()
""").format(
    table=sql.Identifier(*TRAINING_HYPERPARAMETER_QUANTIZE_TABLE),
    method_enum=sql.Identifier(*TRAINING_QUANTIZE_METHOD_ENUM),
    precision_enum=sql.Identifier(*TRAINING_PRECISION_ENUM),
)
