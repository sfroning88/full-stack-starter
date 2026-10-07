from psycopg2 import sql
from fiery_python import (
    TRAINING_SEISMIC_TABLE,
    TRAINING_SESSION_TABLE,
    TRAINING_CONTRACT_TABLE,
    TRAINING_WINDOW_ENUM,
    TRAINING_NORMALIZE_ENUM,
    TRAINING_SIGNAL_ENUM,
)

QUERY = sql.SQL("""
    SELECT training_seismic.id::text,
        training_seismic.nfft,
        training_seismic.hop,
        training_seismic.window::{window_enum},
        training_seismic.window_s,
        training_seismic.sampling_hz,
        training_seismic.mel_bins,
        training_seismic.bandpass_low_hz,
        training_seismic.bandpass_high_hz,
        training_seismic.normalize::{normalize_enum},
        training_seismic.snr_min,
        training_seismic.class_id::text
    FROM {seismic_table} training_seismic
    INNER JOIN {contract_table} training_contract
        ON training_seismic.id = training_contract.seismic_id
    INNER JOIN {session_table} training_session
        ON training_session.contract_id = training_contract.id
    WHERE training_session.id = %s::uuid
        AND training_contract.signal = 'seismic'::{signal_enum}
        AND training_contract.seismic_id IS NOT NULL
""").format(
    seismic_table=sql.Identifier(*TRAINING_SEISMIC_TABLE),
    session_table=sql.Identifier(*TRAINING_SESSION_TABLE),
    contract_table=sql.Identifier(*TRAINING_CONTRACT_TABLE),
    window_enum=sql.Identifier(*TRAINING_WINDOW_ENUM),
    normalize_enum=sql.Identifier(*TRAINING_NORMALIZE_ENUM),
    signal_enum=sql.Identifier(*TRAINING_SIGNAL_ENUM),
)
