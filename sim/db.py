import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "homestead.db"


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS sim_days (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            source           TEXT    NOT NULL DEFAULT 'synthetic',
            created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            -- Weather inputs
            irradiance_wm2   REAL,
            temp_max_c       REAL,
            temp_min_c       REAL,
            outdoor_temp_c   REAL,
            rainfall_mm      REAL,
            peak_sun_hours   REAL,

            -- Solar inputs
            panel_area_m2    REAL,
            house_sqft       REAL,

            -- Crops inputs (JSON array of {crop, land_acres, days_in_season})
            crops_json       TEXT,

            -- Cattle inputs (JSON array of {animal, count})
            cattle_json      TEXT,

            -- Water inputs
            household_persons    INTEGER,
            irrigated_area_m2    REAL,
            storage_liters_start REAL,

            -- Energy outputs
            kwh_produced     REAL,
            kwh_consumed     REAL,
            net_kwh_solar    REAL,
            energy_status    TEXT,

            -- Biogas outputs
            biogas_m3        REAL,
            biogas_kwh       REAL,

            -- Crops outputs
            daily_yield_kg   REAL,
            daily_kcal_crops REAL,
            water_stress     REAL,

            -- Cattle outputs
            milk_liters_day  REAL,
            meat_kg_day      REAL,
            manure_kg_day    REAL,
            kcal_cattle      REAL,

            -- Water outputs
            water_collected_liters  REAL,
            livestock_demand_liters REAL,
            water_supply_ratio      REAL,
            water_status            TEXT,

            -- Summary
            total_kwh_produced  REAL,
            total_kwh_consumed  REAL,
            net_kwh             REAL,
            total_food_kcal     REAL
        );

        CREATE INDEX IF NOT EXISTS idx_source ON sim_days (source);
        CREATE INDEX IF NOT EXISTS idx_net_kwh ON sim_days (net_kwh);
        """)


def insert_sim_day(row: dict) -> int:
    cols = ", ".join(row.keys())
    placeholders = ", ".join("?" for _ in row)
    values = [json.dumps(v) if isinstance(v, (list, dict)) else v for v in row.values()]
    with get_conn() as conn:
        cur = conn.execute(
            f"INSERT INTO sim_days ({cols}) VALUES ({placeholders})", values
        )
        return cur.lastrowid


if __name__ == "__main__":
    init_db()
    print(f"DB initialised at {DB_PATH}")