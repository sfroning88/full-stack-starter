from psycopg2 import sql
from fiery_python import (
    TRAINING_INTERFEROGRAM_TABLE,
    TRAINING_SAMPLE_SOURCE_ENUM,
    TRAINING_SPLIT_ENUM,
    TRAINING_DEFORMATION_LABEL_ENUM,
)

QUERY = sql.SQL("""
    SELECT id::text,
        source::{source_enum},
        split::{split_enum},
        label::{label_enum},
        frame_id,
        primary_at,
        secondary_at,
        coherence_mean,
        is_augmented,
        storage_path,
        deformation_source_id::text,
        volcano_id::text
    FROM {table}
    WHERE split = %s::{split_enum}
        AND id > %s::uuid
    ORDER BY id
    LIMIT %s
""").format(
    table=sql.Identifier(*TRAINING_INTERFEROGRAM_TABLE),
    source_enum=sql.Identifier(*TRAINING_SAMPLE_SOURCE_ENUM),
    split_enum=sql.Identifier(*TRAINING_SPLIT_ENUM),
    label_enum=sql.Identifier(*TRAINING_DEFORMATION_LABEL_ENUM),
)
