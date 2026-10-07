from psycopg2 import sql
from fiery_python import TRAINING_HYPERPARAMETER_DISTILL_TABLE

QUERY = sql.SQL("""
    INSERT INTO {table}
    (
        id,
        temperature,
        alpha,
        epochs,
        batch_size,
        learning_rate,
        student_architecture,
        created_at,
        updated_at
    )
    VALUES (
        %(id)s::uuid,
        %(temperature)s,
        %(alpha)s,
        %(epochs)s,
        %(batch_size)s,
        %(learning_rate)s,
        %(student_architecture)s,
        NOW(),
        NOW()
    )
    ON CONFLICT (id)
    DO UPDATE SET
        temperature = EXCLUDED.temperature,
        alpha = EXCLUDED.alpha,
        epochs = EXCLUDED.epochs,
        batch_size = EXCLUDED.batch_size,
        learning_rate = EXCLUDED.learning_rate,
        student_architecture = EXCLUDED.student_architecture,
        updated_at = NOW()
""").format(table=sql.Identifier(*TRAINING_HYPERPARAMETER_DISTILL_TABLE))
