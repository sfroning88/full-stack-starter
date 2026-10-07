from psycopg2 import sql
from fiery_python import (
    TRAINING_CONTRACT_TABLE,
    TRAINING_SIGNAL_ENUM,
)

QUERY = sql.SQL("""
    SELECT id::text,
        signal::{signal_enum},
        notes,
        version,
        seismic_id::text,
        deformation_id::text
    FROM {table}
    WHERE id = %s::uuid
""").format(
    table=sql.Identifier(*TRAINING_CONTRACT_TABLE),
    signal_enum=sql.Identifier(*TRAINING_SIGNAL_ENUM),
)
