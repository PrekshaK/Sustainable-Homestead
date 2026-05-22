from dataclasses import dataclass
from enum import Enum

# Hargreaves ETo coefficients
_HARG_A = 0.0023
_HARG_OFFSET = 17.8
# Solar constant (MJ/m²/day) at top of atmosphere for mid-latitudes (~30°N, central Texas)
# Real implementation would use lat+DOY; this is a reasonable annual mean
_RA_DEFAULT_MJ = 32.0
# Caloric densities (kcal/kg fresh weight)
_KCAL_PER_KG = {
    "corn": 365,
    "tomato": 180,
    "potato": 770,
    "beans": 1400,
    "wheat": 3400,
}
# Crop coefficients (Kc mid-season, FAO-56 Table 12)
_KC = {
    "corn": 1.20,
    "tomato": 1.15,
    "potato": 1.15,
    "beans": 1.15,
    "wheat": 1.15,
}
# Typical full-season max yields (kg per acre)
_MAX_YIELD_KG_PER_ACRE = {
    "corn": 7_000,
    "tomato": 25_000,
    "potato": 20_000,
    "beans": 2_000,
    "wheat": 2_500,
}
# Full growing season length (days) for yield normalisation
_FULL_SEASON_DAYS = {
    "corn": 120,
    "tomato": 90,
    "potato": 100,
    "beans": 75,
    "wheat": 110,
}


class CropType(str, Enum):
    corn = "corn"
    tomato = "tomato"
    potato = "potato"
    beans = "beans"
    wheat = "wheat"


@dataclass
class CropInputs:
    crop: CropType
    land_acres: float          # planted area (acres)
    rainfall_mm: float         # daily rainfall
    temp_max_c: float          # daily max temperature
    temp_min_c: float          # daily min temperature
    days_in_season: int        # days elapsed in current growing season
    ra_mj_m2: float = _RA_DEFAULT_MJ  # extraterrestrial radiation (override for lat/DOY)


@dataclass
class CropOutputs:
    eto_mm: float              # reference evapotranspiration (mm/day)
    crop_et_mm: float          # crop water demand (mm/day)
    water_stress: float        # 0–1 (1 = no stress)
    daily_yield_kg: float      # estimated fresh-weight yield for this day
    daily_kcal: float          # caloric equivalent
    water_deficit_mm: float    # rainfall − crop_ET (negative = irrigation needed)


def simulate_day(inputs: CropInputs) -> CropOutputs:
    crop = inputs.crop.value

    # --- Reference ET (Hargreaves-Samani) ---
    t_mean = (inputs.temp_max_c + inputs.temp_min_c) / 2.0
    t_range = max(0.0, inputs.temp_max_c - inputs.temp_min_c)
    eto_mm = _HARG_A * (t_mean + _HARG_OFFSET) * (t_range ** 0.5) * inputs.ra_mj_m2

    # --- Crop ET ---
    kc = _KC[crop]
    crop_et_mm = kc * eto_mm

    # --- Water stress (simple ratio; real FAO-56 uses soil water balance) ---
    water_stress = min(1.0, inputs.rainfall_mm / crop_et_mm) if crop_et_mm > 0 else 1.0

    # --- Daily yield fraction ---
    # Linearly accumulate over growing season; stress reduces daily accumulation
    full_season = _FULL_SEASON_DAYS[crop]
    season_fraction = min(1.0, inputs.days_in_season / full_season)
    max_yield = _MAX_YIELD_KG_PER_ACRE[crop] * inputs.land_acres

    # Yield today = marginal gain this day × stress
    daily_fraction = (1.0 / full_season) * water_stress
    daily_yield_kg = max_yield * daily_fraction

    daily_kcal = daily_yield_kg * _KCAL_PER_KG[crop]
    water_deficit_mm = inputs.rainfall_mm - crop_et_mm

    return CropOutputs(
        eto_mm=round(eto_mm, 3),
        crop_et_mm=round(crop_et_mm, 3),
        water_stress=round(water_stress, 4),
        daily_yield_kg=round(daily_yield_kg, 3),
        daily_kcal=round(daily_kcal, 1),
        water_deficit_mm=round(water_deficit_mm, 3),
    )


if __name__ == "__main__":
    scenarios = [
        ("Corn — good summer day",
         CropInputs(crop=CropType.corn, land_acres=2.0,
                    rainfall_mm=6.0, temp_max_c=34, temp_min_c=22, days_in_season=60)),
        ("Tomato — drought stress",
         CropInputs(crop=CropType.tomato, land_acres=0.5,
                    rainfall_mm=0.5, temp_max_c=38, temp_min_c=24, days_in_season=45)),
        ("Wheat — mild spring",
         CropInputs(crop=CropType.wheat, land_acres=3.0,
                    rainfall_mm=4.0, temp_max_c=22, temp_min_c=12, days_in_season=80)),
        ("Potato — well-watered",
         CropInputs(crop=CropType.potato, land_acres=1.0,
                    rainfall_mm=8.0, temp_max_c=25, temp_min_c=14, days_in_season=50)),
    ]

    for label, inp in scenarios:
        out = simulate_day(inp)
        print(f"=== {label} ===")
        print(f"  ETo           : {out.eto_mm:.2f} mm/day")
        print(f"  Crop ET       : {out.crop_et_mm:.2f} mm/day")
        print(f"  Water stress  : {out.water_stress:.2%}")
        print(f"  Daily yield   : {out.daily_yield_kg:.3f} kg")
        print(f"  Daily kcal    : {out.daily_kcal:.0f} kcal")
        print(f"  Water deficit : {out.water_deficit_mm:+.2f} mm")
        print()
