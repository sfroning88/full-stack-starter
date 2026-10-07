from psycopg2 import sql
from fiery_python import (
    TRAINING_INTERFEROGRAM_TABLE,
    TRAINING_SEISMIC_EVENT_TABLE,
    VOLCANO_TABLE,
    VOLCANO_ZONE_ENUM,
)

QUERY = sql.SQL("""
    SELECT id::text,
        gvp_number,
        name,
        country,
        zone::{zone_enum},
        latitude,
        longitude,
        elevation_m,
        volcanic_class,
        is_glaciated,
        is_instrumented,
        is_held_out,
        image_path
    FROM {table}
    WHERE EXISTS (
        SELECT 1
        FROM {interferograms}
        WHERE volcano_id = {table}.id
    )
    OR EXISTS (
        SELECT 1
        FROM {seismic_events}
        WHERE volcano_id = {table}.id
    )
    ORDER BY id
    LIMIT %s
""").format(
    table=sql.Identifier(*VOLCANO_TABLE),
    interferograms=sql.Identifier(*TRAINING_INTERFEROGRAM_TABLE),
    seismic_events=sql.Identifier(*TRAINING_SEISMIC_EVENT_TABLE),
    zone_enum=sql.Identifier(*VOLCANO_ZONE_ENUM),
)
