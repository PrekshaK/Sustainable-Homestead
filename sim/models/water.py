from dataclasses import dataclass

# Household water use — homestead-conserved (US avg ~300 L; off-grid target ~120 L)
_HOUSEHOLD_LITERS_PER_PERSON = 120.0

# Livestock daily water demand
_BEEF_LITERS_PER_HEAD = 40.0    # grazing beef cattle, temperate climate
_DAIRY_LITERS_PER_COW = 90.0    # dairy cows need more (lactation + higher intake)

# Rainwater harvesting
_DEFAULT_ROOF_AREA_M2 = 185.0   # ~2000 sqft house footprint
_COLLECTION_EFF = 0.80           # gutters + first-flush diverter losses

# Status thresholds (supply_ratio = available / demand)
_STRESS_THRESHOLD = 0.70
_CRITICAL_THRESHOLD = 0.30


@dataclass
class WaterInputs:
    rainfall_mm: float              # daily rainfall (mm)
    household_persons: int          # people in the household
    beef_head: int                  # beef cattle count
    dairy_cows: int                 # dairy cow count
    irrigated_area_m2: float        # crop area receiving irrigation (m²)
    crop_et_mm: float               # crop evapotranspiration demand (from crops.py)
    storage_liters: float           # cistern/tank level at start of day (L)
    roof_area_m2: float = _DEFAULT_ROOF_AREA_M2
    collection_efficiency: float = _COLLECTION_EFF
    max_storage_liters: float = 20_000.0  # typical residential rainwater tank


@dataclass
class WaterOutputs:
    # Supply
    rainfall_collected_liters: float

    # Demand breakdown
    household_demand_liters: float
    livestock_demand_liters: float
    irrigation_demand_liters: float
    total_demand_liters: float

    # Balance
    net_liters: float          # collected − demand (before drawing on storage)
    storage_liters: float      # updated tank level at end of day
    supply_ratio: float        # fraction of demand met (0–1)
    status: str                # "sufficient" | "stressed" | "critical"


def simulate_day(inputs: WaterInputs) -> WaterOutputs:
    # --- Rainfall collection ---
    # 1 mm of rain over 1 m² = 1 litre
    rainfall_collected = (
        inputs.rainfall_mm
        * inputs.roof_area_m2
        * inputs.collection_efficiency
    )

    # --- Demand ---
    household_demand = inputs.household_persons * _HOUSEHOLD_LITERS_PER_PERSON

    livestock_demand = (
        inputs.beef_head * _BEEF_LITERS_PER_HEAD
        + inputs.dairy_cows * _DAIRY_LITERS_PER_COW
    )

    # Irrigation: only the deficit between crop ET and what rainfall already provides
    # max(0, crop_et - rainfall) mm, converted to litres over the irrigated area
    irrigation_mm = max(0.0, inputs.crop_et_mm - inputs.rainfall_mm)
    irrigation_demand = irrigation_mm * inputs.irrigated_area_m2  # mm * m² = litres

    total_demand = household_demand + livestock_demand + irrigation_demand

    # --- Storage draw / fill ---
    # Available today = fresh collection + whatever is in the tank
    available = rainfall_collected + inputs.storage_liters

    if available >= total_demand:
        storage_end = min(available - total_demand, inputs.max_storage_liters)
        supply_ratio = 1.0
    else:
        storage_end = 0.0
        supply_ratio = available / total_demand if total_demand > 0 else 1.0

    net_liters = rainfall_collected - total_demand

    if supply_ratio >= _STRESS_THRESHOLD:
        status = "sufficient"
    elif supply_ratio >= _CRITICAL_THRESHOLD:
        status = "stressed"
    else:
        status = "critical"

    return WaterOutputs(
        rainfall_collected_liters=round(rainfall_collected, 1),
        household_demand_liters=round(household_demand, 1),
        livestock_demand_liters=round(livestock_demand, 1),
        irrigation_demand_liters=round(irrigation_demand, 1),
        total_demand_liters=round(total_demand, 1),
        net_liters=round(net_liters, 1),
        storage_liters=round(storage_end, 1),
        supply_ratio=round(supply_ratio, 4),
        status=status,
    )


if __name__ == "__main__":
    scenarios = [
        ("Good rain day — full homestead",
         WaterInputs(
             rainfall_mm=15.0, household_persons=4,
             beef_head=2, dairy_cows=1,
             irrigated_area_m2=2000, crop_et_mm=8.0,
             storage_liters=10_000,
         )),
        ("Dry summer day — full homestead",
         WaterInputs(
             rainfall_mm=0.5, household_persons=4,
             beef_head=2, dairy_cows=1,
             irrigated_area_m2=2000, crop_et_mm=12.0,
             storage_liters=10_000,
         )),
        ("Drought — empty tank",
         WaterInputs(
             rainfall_mm=0.0, household_persons=4,
             beef_head=5, dairy_cows=2,
             irrigated_area_m2=3000, crop_et_mm=14.0,
             storage_liters=500,
         )),
        ("Minimal setup — no livestock, small garden",
         WaterInputs(
             rainfall_mm=5.0, household_persons=2,
             beef_head=0, dairy_cows=0,
             irrigated_area_m2=200, crop_et_mm=6.0,
             storage_liters=5_000,
         )),
    ]

    for label, inp in scenarios:
        out = simulate_day(inp)
        print(f"=== {label} ===")
        print(f"  Collected     : {out.rainfall_collected_liters:7.1f} L")
        print(f"  Household     : {out.household_demand_liters:7.1f} L")
        print(f"  Livestock     : {out.livestock_demand_liters:7.1f} L")
        print(f"  Irrigation    : {out.irrigation_demand_liters:7.1f} L")
        print(f"  Total demand  : {out.total_demand_liters:7.1f} L")
        print(f"  Supply ratio  : {out.supply_ratio:.1%}  [{out.status}]")
        print(f"  Tank end-of-day: {out.storage_liters:,.0f} L")
        print()
