from psycopg2 import sql
from fiery_python import TRAINING_HYPERPARAMETER_DISTILL_TABLE

QUERY = sql.SQL("""
    SELECT id::text,
        temperature,
        alpha,
        epochs,
        batch_size,
        learning_rate,
        student_architecture
    FROM {table}
    WHERE id = %s::uuid
    ORDER BY created_at DESC
    LIMIT 1
""").format(table=sql.Identifier(*TRAINING_HYPERPARAMETER_DISTILL_TABLE))
