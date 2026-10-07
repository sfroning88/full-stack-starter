from psycopg2 import sql
from fiery_python import (
    TRAINING_DEFORMATION_TABLE,
    TRAINING_SESSION_TABLE,
    TRAINING_CONTRACT_TABLE,
    TRAINING_NORMALIZE_ENUM,
    TRAINING_SIGNAL_ENUM,
)

QUERY = sql.SQL("""
    SELECT training_deformation.id::text,
        training_deformation.patch_px,
        training_deformation.wrap_rad,
        training_deformation.normalize::{normalize_enum},
        training_deformation.coherence_min,
        training_deformation.class_id::text
    FROM {deformation_table} training_deformation
    INNER JOIN {contract_table} training_contract
        ON training_deformation.id = training_contract.deformation_id
    INNER JOIN {session_table} training_session
        ON training_session.contract_id = training_contract.id
    WHERE training_session.id = %s::uuid
        AND training_contract.signal = 'deformation'::{signal_enum}
        AND training_contract.deformation_id IS NOT NULL
""").format(
    deformation_table=sql.Identifier(*TRAINING_DEFORMATION_TABLE),
    session_table=sql.Identifier(*TRAINING_SESSION_TABLE),
    contract_table=sql.Identifier(*TRAINING_CONTRACT_TABLE),
    normalize_enum=sql.Identifier(*TRAINING_NORMALIZE_ENUM),
    signal_enum=sql.Identifier(*TRAINING_SIGNAL_ENUM),
)
