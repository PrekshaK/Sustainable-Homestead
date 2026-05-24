"""
Generate synthetic simulation days and store them in SQLite.

Usage:
    python -m sim.data.synthetic            # 10 000 rows (default)
    python -m sim.data.synthetic --n 500    # custom count
"""

import argparse
import json
import random
import sys
from pathlib import Path

import sim.models.energy_balance as eb
import sim.models.biogas as bg
import sim.models.crops as cr
import sim.models.cattle as ca
import sim.models.water as wt
from sim.models.crops import CropType
from sim.db import init_db, insert_sim_day

# ── Parameter ranges (central Texas climate, homestead scale) ─────────────────

CROP_TYPES   = [c.value for c in CropType]
ANIMAL_TYPES = list(ca._SP.keys())

def _sample_weather() -> dict:
    irradiance = random.uniform(50, 1150)
    temp_max   = random.uniform(5, 45)
    # temp_min must be below temp_max; typical diurnal range 8–18 °C
    temp_min   = temp_max - random.uniform(6, 18)
    temp_min   = max(-10, temp_min)

    # Rainfall: most days dry; occasional rain events
    if random.random() < 0.65:
        rainfall = 0.0
    else:
        rainfall = random.expovariate(1 / 12)   # mean ~12 mm on wet days
        rainfall = min(rainfall, 120)

    peak_sun = random.uniform(2, 12)
    return dict(
        irradiance_wm2=round(irradiance, 1),
        temp_max_c=round(temp_max, 1),
        temp_min_c=round(temp_min, 1),
        outdoor_temp_c=round((temp_max + temp_min) / 2, 1),
        rainfall_mm=round(rainfall, 2),
        peak_sun_hours=round(peak_sun, 1),
    )


def _sample_solar() -> dict:
    return dict(
        panel_area_m2=round(random.uniform(10, 120), 1),
        house_sqft=round(random.uniform(800, 5000), 0),
        panel_efficiency=round(random.uniform(0.15, 0.23), 3),
    )


def _sample_crops() -> list[dict]:
    n = random.randint(1, 3)
    chosen = random.sample(CROP_TYPES, n)
    return [
        dict(
            crop=c,
            land_acres=round(random.uniform(0.5, 8), 1),
            days_in_season=random.randint(30, 150),
        )
        for c in chosen
    ]


def _sample_cattle() -> list[dict]:
    # 20 % chance of no livestock at all
    if random.random() < 0.20:
        return []
    n_species = random.randint(1, 3)
    chosen = random.sample(ANIMAL_TYPES, n_species)
    return [
        dict(animal=a, count=random.randint(1, 20))
        for a in chosen
    ]


def _sample_water(n_crops: int) -> dict:
    return dict(
        household_persons=random.randint(1, 8),
        irrigated_area_m2=round(random.uniform(0, 4000), 0),
        storage_liters=round(random.uniform(0, 20_000), 0),
    )


# ── Run one simulation day ────────────────────────────────────────────────────

def run_one() -> dict:
    w  = _sample_weather()
    s  = _sample_solar()
    crops_cfg  = _sample_crops()
    cattle_cfg = _sample_cattle()
    water_cfg  = _sample_water(len(crops_cfg))

    # Energy
    energy = eb.simulate_day(eb.EnergyInputs(
        irradiance_wm2=w['irradiance_wm2'],
        panel_area_m2=s['panel_area_m2'],
        house_sqft=s['house_sqft'],
        outdoor_temp_c=w['outdoor_temp_c'],
        peak_sun_hours=w['peak_sun_hours'],
        panel_efficiency=s['panel_efficiency'],
    ))

    # Cattle → biogas chain
    herd = [(e['animal'], e['count']) for e in cattle_cfg]
    cattle = ca.simulate_day(ca.CattleInputs(herd=herd))

    biogas = bg.simulate_day(bg.BiogasInputs(
        organic_waste_kg=cattle.manure_kg_day,
        temp_c=35,
        vs_fraction=cattle.vs_fraction,
        specific_yield_m3_per_kg_vs=0.22,
    ))

    # Crops
    crop_results = [
        cr.simulate_day(cr.CropInputs(
            crop=CropType(c['crop']),
            land_acres=c['land_acres'],
            rainfall_mm=w['rainfall_mm'],
            temp_max_c=w['temp_max_c'],
            temp_min_c=w['temp_min_c'],
            days_in_season=c['days_in_season'],
        ))
        for c in crops_cfg
    ]
    total_acres = sum(c['land_acres'] for c in crops_cfg)

    def _wavg(field):
        return sum(getattr(r, field) * c['land_acres'] for r, c in zip(crop_results, crops_cfg)) / total_acres

    crop_et_mm = round(_wavg('crop_et_mm'), 3)
    daily_yield_kg = round(sum(r.daily_yield_kg for r in crop_results), 3)
    daily_kcal_crops = round(sum(r.daily_kcal for r in crop_results), 1)
    water_stress = round(_wavg('water_stress'), 4)

    # Water
    water = wt.simulate_day(wt.WaterInputs(
        rainfall_mm=w['rainfall_mm'],
        household_persons=water_cfg['household_persons'],
        livestock_liters_day=cattle.water_liters_day,
        irrigated_area_m2=water_cfg['irrigated_area_m2'],
        crop_et_mm=crop_et_mm,
        storage_liters=water_cfg['storage_liters'],
    ))

    total_kwh_produced = round(energy.kwh_produced + biogas.kwh_equivalent, 3)
    net_kwh = round(total_kwh_produced - energy.kwh_consumed, 3)

    return dict(
        source='synthetic',

        # Inputs
        irradiance_wm2=w['irradiance_wm2'],
        temp_max_c=w['temp_max_c'],
        temp_min_c=w['temp_min_c'],
        outdoor_temp_c=w['outdoor_temp_c'],
        rainfall_mm=w['rainfall_mm'],
        peak_sun_hours=w['peak_sun_hours'],
        panel_area_m2=s['panel_area_m2'],
        house_sqft=s['house_sqft'],
        crops_json=json.dumps(crops_cfg),
        cattle_json=json.dumps(cattle_cfg),
        household_persons=water_cfg['household_persons'],
        irrigated_area_m2=water_cfg['irrigated_area_m2'],
        storage_liters_start=water_cfg['storage_liters'],

        # Energy outputs
        kwh_produced=energy.kwh_produced,
        kwh_consumed=energy.kwh_consumed,
        net_kwh_solar=energy.net_kwh,
        energy_status=energy.status,

        # Biogas outputs
        biogas_m3=biogas.biogas_m3,
        biogas_kwh=biogas.kwh_equivalent,

        # Crops outputs
        daily_yield_kg=daily_yield_kg,
        daily_kcal_crops=daily_kcal_crops,
        water_stress=water_stress,

        # Cattle outputs
        milk_liters_day=cattle.milk_liters_day,
        meat_kg_day=cattle.meat_kg_day,
        manure_kg_day=cattle.manure_kg_day,
        kcal_cattle=cattle.kcal_day,

        # Water outputs
        water_collected_liters=water.rainfall_collected_liters,
        livestock_demand_liters=water.livestock_demand_liters,
        water_supply_ratio=water.supply_ratio,
        water_status=water.status,

        # Summary
        total_kwh_produced=total_kwh_produced,
        total_kwh_consumed=energy.kwh_consumed,
        net_kwh=net_kwh,
        total_food_kcal=round(daily_kcal_crops + cattle.kcal_day, 1),
    )


# ── CLI entry point ───────────────────────────────────────────────────────────

def main(n: int = 10_000) -> None:
    init_db()
    print(f"Generating {n:,} synthetic days...", flush=True)

    for i in range(1, n + 1):
        row = run_one()
        insert_sim_day(row)

        if i % 500 == 0 or i == n:
            pct = i / n * 100
            bar = "#" * (i * 20 // n)
            sys.stdout.write(f"\r  [{bar:<20}] {pct:.0f}%  ({i:,}/{n:,})")
            sys.stdout.flush()

    print(f"\nDone. {n:,} rows written.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=10_000, help="number of days to generate")
    args = parser.parse_args()
    main(args.n)