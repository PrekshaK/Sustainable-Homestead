"""
Pull historical daily weather from NOAA CDO API, run it through the sim,
and store each day in SQLite with source='noaa'.

Usage:
    python -m sim.data.weather \\
        --station GHCND:USW00013958 \\
        --lat 30.2 \\
        --start 2018-01-01 \\
        --end 2023-12-31

How to find your station ID:
    1. Go to https://www.ncdc.noaa.gov/cdo-web/datatools/findstation
    2. Search by city or zip, filter by dataset "Daily Summaries"
    3. Click a station — the ID (e.g. GHCND:USW00013958) is in the URL

The NOAA_API_TOKEN must be set in your .env file (project root).
Get a free token at: https://www.ncdc.noaa.gov/cdo-web/token
"""

import argparse
import json
import math
import os
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

import sim.models.energy_balance as eb
import sim.models.biogas as bg
import sim.models.crops as cr
import sim.models.cattle as ca
import sim.models.water as wt
from sim.models.crops import CropType
from sim.db import init_db, insert_sim_day

load_dotenv(Path(__file__).parent.parent.parent / ".env")

NOAA_BASE = "https://www.ncdc.noaa.gov/cdo-web/api/v2"

# Fixed representative homestead — only weather varies in this dataset
_HOMESTEAD = dict(
    panel_area_m2=40,
    house_sqft=2000,
    panel_efficiency=0.20,
    crops=[
        dict(crop="corn",   land_acres=2, days_in_season=90),
        dict(crop="beans",  land_acres=1, days_in_season=60),
    ],
    cattle=[
        dict(animal="cow",     count=2),
        dict(animal="chicken", count=10),
    ],
    household_persons=4,
    irrigated_area_m2=2000,
    storage_liters=10_000,
)


# ── Solar estimation (Hargreaves-Samani, FAO-56) ──────────────────────────────

def _extraterrestrial_radiation(lat_deg: float, doy: int) -> float:
    """Ra in MJ/m²/day."""
    lat  = math.radians(lat_deg)
    dr   = 1 + 0.033 * math.cos(2 * math.pi * doy / 365)
    decl = 0.409 * math.sin(2 * math.pi * doy / 365 - 1.39)
    ws   = math.acos(max(-1, min(1, -math.tan(lat) * math.tan(decl))))
    Ra   = (24 * 60 / math.pi) * 0.0820 * dr * (
        ws * math.sin(lat) * math.sin(decl)
        + math.cos(lat) * math.cos(decl) * math.sin(ws)
    )
    return Ra


def _estimate_solar(tmax_c: float, tmin_c: float, lat_deg: float, doy: int) -> tuple:
    """Return (irradiance_wm2, peak_sun_hours) estimated from temp range."""
    Ra = _extraterrestrial_radiation(lat_deg, doy)
    # kRs = 0.16 for interior/continental, 0.19 for coastal
    Rs = Ra * 0.16 * math.sqrt(max(0.0, tmax_c - tmin_c))  # MJ/m²/day
    irradiance_wm2  = Rs * 1_000_000 / 86_400               # W/m²
    peak_sun_hours  = Rs * 1_000_000 / 3_600_000            # kWh/m² = PSH
    return round(max(0, irradiance_wm2), 1), round(max(0, peak_sun_hours), 2)


# ── NOAA API calls ────────────────────────────────────────────────────────────

def _get_token() -> str:
    token = os.environ.get("NOAA_API_TOKEN", "")
    if not token or token == "your_token_here":
        sys.exit(
            "ERROR: NOAA_API_TOKEN not set.\n"
            "Add it to your .env file: NOAA_API_TOKEN=your_token_here\n"
            "Get a free token at: https://www.ncdc.noaa.gov/cdo-web/token"
        )
    return token


def _noaa_get(path: str, token: str, params: dict) -> dict:
    """Single NOAA CDO API request with rate-limit backoff."""
    headers = {"token": token}
    url = f"{NOAA_BASE}/{path}"
    for attempt in range(3):
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        if resp.status_code == 429:
            time.sleep(2 ** attempt)
            continue
        resp.raise_for_status()
        return resp.json()
    resp.raise_for_status()


def _year_chunks(start: date, end: date):
    """Yield (chunk_start, chunk_end) pairs split by calendar year."""
    cur = start
    while cur <= end:
        chunk_end = min(date(cur.year, 12, 31), end)
        yield cur, chunk_end
        cur = date(cur.year + 1, 1, 1)


def _fetch_year(station_id: str, chunk_start: date, chunk_end: date,
                token: str, records: dict) -> None:
    """Fetch one year-chunk with pagination into the shared records dict."""
    offset = 1
    total  = None
    while total is None or offset <= total:
        params = dict(
            datasetid="GHCND",
            stationid=station_id,
            datatypeid="TMAX,TMIN,PRCP",
            startdate=chunk_start.isoformat(),
            enddate=chunk_end.isoformat(),
            units="metric",
            limit=1000,
            offset=offset,
        )
        data  = _noaa_get("data", token, params)
        total = data.get("metadata", {}).get("resultset", {}).get("count", 0)
        for rec in data.get("results", []):
            d  = rec["date"][:10]
            records.setdefault(d, {})[rec["datatype"]] = rec["value"]
        offset += 1000
        time.sleep(0.25)


def fetch_daily_weather(station_id: str, start: date, end: date, token: str) -> list[dict]:
    """
    Fetch TMAX, TMIN, PRCP for a station and date range.
    Splits into 1-year chunks (NOAA API limit) and paginates each.
    Returns list of {date, tmax_c, tmin_c, prcp_mm}.
    """
    records: dict[str, dict] = {}

    chunks = list(_year_chunks(start, end))
    for i, (cs, ce) in enumerate(chunks, 1):
        print(f"  Fetching {cs.year} ({i}/{len(chunks)})...", end=" ", flush=True)
        _fetch_year(station_id, cs, ce, token, records)
        print("done")
        time.sleep(0.5)

    # Build clean day list — skip days with missing temperature
    days = []
    for d, vals in sorted(records.items()):
        if "TMAX" not in vals or "TMIN" not in vals:
            continue
        days.append(dict(
            date=d,
            tmax_c=round(vals["TMAX"], 1),
            tmin_c=round(vals["TMIN"], 1),
            prcp_mm=round(vals.get("PRCP", 0.0), 2),
        ))

    return days


# ── Sim runner ────────────────────────────────────────────────────────────────

def _run_day(weather: dict, lat_deg: float) -> dict:
    doy = date.fromisoformat(weather["date"]).timetuple().tm_yday
    tmax, tmin = weather["tmax_c"], weather["tmin_c"]
    prcp = weather["prcp_mm"]
    outdoor_temp_c = round((tmax + tmin) / 2, 1)

    irradiance_wm2, peak_sun_hours = _estimate_solar(tmax, tmin, lat_deg, doy)

    h = _HOMESTEAD

    energy = eb.simulate_day(eb.EnergyInputs(
        irradiance_wm2=irradiance_wm2,
        panel_area_m2=h["panel_area_m2"],
        house_sqft=h["house_sqft"],
        outdoor_temp_c=outdoor_temp_c,
        peak_sun_hours=peak_sun_hours,
        panel_efficiency=h["panel_efficiency"],
    ))

    herd   = [(e["animal"], e["count"]) for e in h["cattle"]]
    cattle = ca.simulate_day(ca.CattleInputs(herd=herd))

    biogas = bg.simulate_day(bg.BiogasInputs(
        organic_waste_kg=cattle.manure_kg_day,
        temp_c=35,
        vs_fraction=cattle.vs_fraction,
        specific_yield_m3_per_kg_vs=0.22,
    ))

    crop_results = [
        cr.simulate_day(cr.CropInputs(
            crop=CropType(c["crop"]),
            land_acres=c["land_acres"],
            rainfall_mm=prcp,
            temp_max_c=tmax,
            temp_min_c=tmin,
            days_in_season=c["days_in_season"],
        ))
        for c in h["crops"]
    ]
    total_acres = sum(c["land_acres"] for c in h["crops"])

    def _wavg(field):
        return sum(getattr(r, field) * c["land_acres"] for r, c in zip(crop_results, h["crops"])) / total_acres

    crop_et_mm       = round(_wavg("crop_et_mm"), 3)
    daily_yield_kg   = round(sum(r.daily_yield_kg for r in crop_results), 3)
    daily_kcal_crops = round(sum(r.daily_kcal for r in crop_results), 1)
    water_stress     = round(_wavg("water_stress"), 4)

    water = wt.simulate_day(wt.WaterInputs(
        rainfall_mm=prcp,
        household_persons=h["household_persons"],
        livestock_liters_day=cattle.water_liters_day,
        irrigated_area_m2=h["irrigated_area_m2"],
        crop_et_mm=crop_et_mm,
        storage_liters=h["storage_liters"],
    ))

    total_kwh_produced = round(energy.kwh_produced + biogas.kwh_equivalent, 3)
    net_kwh            = round(total_kwh_produced - energy.kwh_consumed, 3)

    return dict(
        source="noaa",

        irradiance_wm2=irradiance_wm2,
        temp_max_c=tmax,
        temp_min_c=tmin,
        outdoor_temp_c=outdoor_temp_c,
        rainfall_mm=prcp,
        peak_sun_hours=peak_sun_hours,
        panel_area_m2=h["panel_area_m2"],
        house_sqft=h["house_sqft"],
        crops_json=json.dumps(h["crops"]),
        cattle_json=json.dumps(h["cattle"]),
        household_persons=h["household_persons"],
        irrigated_area_m2=h["irrigated_area_m2"],
        storage_liters_start=h["storage_liters"],

        kwh_produced=energy.kwh_produced,
        kwh_consumed=energy.kwh_consumed,
        net_kwh_solar=energy.net_kwh,
        energy_status=energy.status,

        biogas_m3=biogas.biogas_m3,
        biogas_kwh=biogas.kwh_equivalent,

        daily_yield_kg=daily_yield_kg,
        daily_kcal_crops=daily_kcal_crops,
        water_stress=water_stress,

        milk_liters_day=cattle.milk_liters_day,
        meat_kg_day=cattle.meat_kg_day,
        manure_kg_day=cattle.manure_kg_day,
        kcal_cattle=cattle.kcal_day,

        water_collected_liters=water.rainfall_collected_liters,
        livestock_demand_liters=water.livestock_demand_liters,
        water_supply_ratio=water.supply_ratio,
        water_status=water.status,

        total_kwh_produced=total_kwh_produced,
        total_kwh_consumed=energy.kwh_consumed,
        net_kwh=net_kwh,
        total_food_kcal=round(daily_kcal_crops + cattle.kcal_day, 1),
    )


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch NOAA weather and run sim")
    parser.add_argument("--station", required=True,
                        help="NOAA station ID, e.g. GHCND:USW00013958")
    parser.add_argument("--lat", type=float, required=True,
                        help="Station latitude in decimal degrees (for solar estimation)")
    parser.add_argument("--start", required=True, help="Start date YYYY-MM-DD")
    parser.add_argument("--end",   required=True, help="End date YYYY-MM-DD")
    args = parser.parse_args()

    token = _get_token()
    init_db()

    start = date.fromisoformat(args.start)
    end   = date.fromisoformat(args.end)

    print(f"Fetching weather from NOAA: {args.station} ({args.start} → {args.end})")
    days = fetch_daily_weather(args.station, start, end, token)
    print(f"Retrieved {len(days):,} days with complete temperature data.")

    print("Running sim and storing rows...")
    for i, w in enumerate(days, 1):
        row = _run_day(w, args.lat)
        insert_sim_day(row)
        if i % 100 == 0 or i == len(days):
            sys.stdout.write(f"\r  {i:,}/{len(days):,}")
            sys.stdout.flush()

    print(f"\nDone. {len(days):,} NOAA rows written.")


if __name__ == "__main__":
    main()