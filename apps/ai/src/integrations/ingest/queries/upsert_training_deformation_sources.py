from psycopg2 import sql
from fiery_python import (
    TRAINING_DEFORMATION_SOURCE_TABLE,
    TRAINING_DEFORMATION_SOURCE_TYPE_ENUM,
    TRAINING_NOISE_MODEL_ENUM,
)

QUERY = sql.SQL("""
    INSERT INTO {table}
    (
        id,
        source,
        latitude,
        longitude,
        depth_km,
        volume_change_m3,
        pressure_change_pa,
        strike_deg,
        dip_deg,
        length_km,
        width_km,
        rake_deg,
        slip_m,
        opening_m,
        poissons_ratio,
        shear_modulus_pa,
        los_incidence_deg,
        los_heading_deg,
        wavelength_m,
        noise_model,
        created_at,
        updated_at
    )
    VALUES %s
    ON CONFLICT (id)
    DO UPDATE SET
        source = EXCLUDED.source,
        latitude = EXCLUDED.latitude,
        longitude = EXCLUDED.longitude,
        depth_km = EXCLUDED.depth_km,
        volume_change_m3 = EXCLUDED.volume_change_m3,
        pressure_change_pa = EXCLUDED.pressure_change_pa,
        strike_deg = EXCLUDED.strike_deg,
        dip_deg = EXCLUDED.dip_deg,
        length_km = EXCLUDED.length_km,
        width_km = EXCLUDED.width_km,
        rake_deg = EXCLUDED.rake_deg,
        slip_m = EXCLUDED.slip_m,
        opening_m = EXCLUDED.opening_m,
        poissons_ratio = EXCLUDED.poissons_ratio,
        shear_modulus_pa = EXCLUDED.shear_modulus_pa,
        los_incidence_deg = EXCLUDED.los_incidence_deg,
        los_heading_deg = EXCLUDED.los_heading_deg,
        wavelength_m = EXCLUDED.wavelength_m,
        noise_model = EXCLUDED.noise_model,
        updated_at = NOW()
""").format(table=sql.Identifier(*TRAINING_DEFORMATION_SOURCE_TABLE))

TEMPLATE = sql.SQL("""
    (
        %(id)s::uuid,
        %(source)s::{source_enum},
        %(latitude)s,
        %(longitude)s,
        %(depth_km)s,
        %(volume_change_m3)s,
        %(pressure_change_pa)s,
        %(strike_deg)s,
        %(dip_deg)s,
        %(length_km)s,
        %(width_km)s,
        %(rake_deg)s,
        %(slip_m)s,
        %(opening_m)s,
        %(poissons_ratio)s,
        %(shear_modulus_pa)s,
        %(los_incidence_deg)s,
        %(los_heading_deg)s,
        %(wavelength_m)s,
        %(noise_model)s::{noise_enum},
        NOW(),
        NOW()
    )
""").format(
    source_enum=sql.Identifier(*TRAINING_DEFORMATION_SOURCE_TYPE_ENUM),
    noise_enum=sql.Identifier(*TRAINING_NOISE_MODEL_ENUM),
)
