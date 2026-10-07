from psycopg2 import sql
from fiery_python import MODEL_BUDGET_TABLE

QUERY = sql.SQL("""
    INSERT INTO {table}
    (
        id,
        flash_kb,
        flash_budget_kb,
        peak_ram_kb,
        peak_ram_budget_kb,
        macs,
        macs_budget,
        latency_ms,
        energy_mj,
        days_autonomy,
        passed,
        checked_at,
        artifact_id,
        created_at,
        updated_at
    )
    VALUES (
        %(id)s::uuid,
        %(flash_kb)s,
        %(flash_budget_kb)s,
        %(peak_ram_kb)s,
        %(peak_ram_budget_kb)s,
        %(macs)s,
        %(macs_budget)s,
        %(latency_ms)s,
        %(energy_mj)s,
        %(days_autonomy)s,
        %(passed)s,
        %(checked_at)s,
        %(artifact_id)s::uuid,
        NOW(),
        NOW()
    )
    ON CONFLICT (id)
    DO UPDATE SET
        flash_kb = EXCLUDED.flash_kb,
        flash_budget_kb = EXCLUDED.flash_budget_kb,
        peak_ram_kb = EXCLUDED.peak_ram_kb,
        peak_ram_budget_kb = EXCLUDED.peak_ram_budget_kb,
        macs = EXCLUDED.macs,
        macs_budget = EXCLUDED.macs_budget,
        latency_ms = EXCLUDED.latency_ms,
        energy_mj = EXCLUDED.energy_mj,
        days_autonomy = EXCLUDED.days_autonomy,
        passed = EXCLUDED.passed,
        checked_at = COALESCE(EXCLUDED.checked_at, {table}.checked_at),
        artifact_id = EXCLUDED.artifact_id,
        updated_at = NOW()
""").format(table=sql.Identifier(*MODEL_BUDGET_TABLE))
