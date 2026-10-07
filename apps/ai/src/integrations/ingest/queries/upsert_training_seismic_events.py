from psycopg2 import sql
from fiery_python import (
    TRAINING_SEISMIC_EVENT_TABLE,
    TRAINING_SAMPLE_SOURCE_ENUM,
    TRAINING_SPLIT_ENUM,
    TRAINING_SEISMIC_LABEL_ENUM,
)

QUERY = sql.SQL("""
    INSERT INTO {table}
    (
        id,
        source,
        split,
        label,
        station,
        recorded_at,
        duration_s,
        sampling_hz,
        waveform_path,
        spectrogram_path,
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
        station = EXCLUDED.station,
        recorded_at = EXCLUDED.recorded_at,
        duration_s = EXCLUDED.duration_s,
        sampling_hz = EXCLUDED.sampling_hz,
        waveform_path = EXCLUDED.waveform_path,
        spectrogram_path = EXCLUDED.spectrogram_path,
        volcano_id = EXCLUDED.volcano_id,
        updated_at = NOW()
""").format(table=sql.Identifier(*TRAINING_SEISMIC_EVENT_TABLE))

TEMPLATE = sql.SQL("""
    (
        %(id)s::uuid,
        %(source)s::{source_enum},
        %(split)s::{split_enum},
        %(label)s::{label_enum},
        %(station)s,
        %(recorded_at)s,
        %(duration_s)s,
        %(sampling_hz)s,
        %(waveform_path)s,
        %(spectrogram_path)s,
        %(volcano_id)s::uuid,
        NOW(),
        NOW()
    )
""").format(
    split_enum=sql.Identifier(*TRAINING_SPLIT_ENUM),
    source_enum=sql.Identifier(*TRAINING_SAMPLE_SOURCE_ENUM),
    label_enum=sql.Identifier(*TRAINING_SEISMIC_LABEL_ENUM),
)
