from psycopg2 import sql
from fiery_python import (
    TRAINING_INTERFEROGRAM_TABLE,
    TRAINING_SAMPLE_SOURCE_ENUM,
    TRAINING_SPLIT_ENUM,
    TRAINING_DEFORMATION_LABEL_ENUM,
)

QUERY = sql.SQL("""
    INSERT INTO {table}
    (
        id,
        source,
        split,
        label,
        frame_id,
        primary_at,
        secondary_at,
        coherence_mean,
        is_augmented,
        storage_path,
        deformation_source_id,
        volcano_id,
        created_at,
        updated_at
    )
    VALUES %s
    ON CONFLICT (id)
    DO UPDATE SET
        source = EXCLUDED.source,
        split = EXCLUDED.split,
        label = EXCLUDED.label,
        frame_id = EXCLUDED.frame_id,
        primary_at = EXCLUDED.primary_at,
        secondary_at = EXCLUDED.secondary_at,
        coherence_mean = EXCLUDED.coherence_mean,
        is_augmented = EXCLUDED.is_augmented,
        storage_path = EXCLUDED.storage_path,
        deformation_source_id = EXCLUDED.deformation_source_id,
        volcano_id = EXCLUDED.volcano_id,
        updated_at = NOW()
""").format(table=sql.Identifier(*TRAINING_INTERFEROGRAM_TABLE))

TEMPLATE = sql.SQL("""
    (
        %(id)s::uuid,
        %(source)s::{source_enum},
        %(split)s::{split_enum},
        %(label)s::{label_enum},
        %(frame_id)s,
        %(primary_at)s,
        %(secondary_at)s,
        %(coherence_mean)s,
        %(is_augmented)s,
        %(storage_path)s,
        %(deformation_source_id)s::uuid,
        %(volcano_id)s::uuid,
        NOW(),
        NOW()
    )
""").format(
    split_enum=sql.Identifier(*TRAINING_SPLIT_ENUM),
    source_enum=sql.Identifier(*TRAINING_SAMPLE_SOURCE_ENUM),
    label_enum=sql.Identifier(*TRAINING_DEFORMATION_LABEL_ENUM),
)
