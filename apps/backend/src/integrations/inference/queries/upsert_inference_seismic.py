from psycopg2 import sql
from fiery_python import (
    INFERENCE_SEISMIC_TABLE,
    TRAINING_SEISMIC_LABEL_ENUM,
    INFERENCE_ABSTAIN_REASON_ENUM,
)

QUERY = sql.SQL("""
    INSERT INTO {table}
    (
        label,
        probabilities,
        class_order,
        threshold_used,
        abstention_band,
        abstained,
        abstained_reason,
        transform_hash,
        op_version,
        latency_ms,
        inferred_at,
        artifact_id,
        seismic_event_id,
        created_at,
        updated_at
    )
    VALUES (
        %(label)s::{label_enum},
        %(probabilities)s,
        %(class_order)s::{label_enum}[],
        %(threshold_used)s,
        %(abstention_band)s,
        %(abstained)s,
        %(abstained_reason)s::{reason_enum},
        %(transform_hash)s,
        %(op_version)s,
        %(latency_ms)s,
        %(inferred_at)s,
        %(artifact_id)s::uuid,
        %(seismic_event_id)s::uuid,
        NOW(),
        NOW()
    )
    ON CONFLICT (artifact_id, seismic_event_id)
    DO UPDATE SET
        label = EXCLUDED.label,
        probabilities = EXCLUDED.probabilities,
        class_order = EXCLUDED.class_order,
        threshold_used = EXCLUDED.threshold_used,
        abstention_band = EXCLUDED.abstention_band,
        abstained = EXCLUDED.abstained,
        abstained_reason = COALESCE(EXCLUDED.abstained_reason, {table}.abstained_reason),
        transform_hash = EXCLUDED.transform_hash,
        op_version = EXCLUDED.op_version,
        latency_ms = EXCLUDED.latency_ms,
        inferred_at = COALESCE(EXCLUDED.inferred_at, {table}.inferred_at),
        updated_at = NOW()
""").format(
    table=sql.Identifier(*INFERENCE_SEISMIC_TABLE),
    label_enum=sql.Identifier(*TRAINING_SEISMIC_LABEL_ENUM),
    reason_enum=sql.Identifier(*INFERENCE_ABSTAIN_REASON_ENUM),
)
