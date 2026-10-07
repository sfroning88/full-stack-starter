from psycopg2 import sql
from fiery_python import (
    TRAINING_SEISMIC_EVENT_TABLE,
    TRAINING_SAMPLE_SOURCE_ENUM,
    TRAINING_SPLIT_ENUM,
    TRAINING_SEISMIC_LABEL_ENUM,
)

QUERY = sql.SQL("""
    SELECT id::text,
        source::{source_enum},
        split::{split_enum},
        label::{label_enum},
        station,
        recorded_at,
        duration_s,
        sampling_hz,
        waveform_path,
        spectrogram_path,
        volcano_id::text
    FROM {table}
    WHERE id = %s::uuid
        OR volcano_id = %s::uuid
    ORDER BY created_at DESC
    LIMIT 1
""").format(
    table=sql.Identifier(*TRAINING_SEISMIC_EVENT_TABLE),
    source_enum=sql.Identifier(*TRAINING_SAMPLE_SOURCE_ENUM),
    split_enum=sql.Identifier(*TRAINING_SPLIT_ENUM),
    label_enum=sql.Identifier(*TRAINING_SEISMIC_LABEL_ENUM),
)
