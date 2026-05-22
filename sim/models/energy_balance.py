from dataclasses import dataclass, field

# Standard test conditions reference temperature (°C)
_STC_TEMP_C = 25.0
# Mono/poly-crystalline silicon power temperature coefficient (%/°C)
_TEMP_COEFF = -0.004
# Nominal Operating Cell Temperature (typical mono-PERC panel)
_NOCT_C = 45.0
# Inverter + DC wiring combined efficiency
_SYSTEM_EFF = 0.85

# House load model (EIA-calibrated for US single-family)
_BASE_KWH_PER_SQFT = 0.012          # lighting, appliances, always-on loads
_COOL_KWH_PER_SQFT_PER_DEG = 0.0020 # per °C above comfort ceiling (COP ~2.5)
_HEAT_KWH_PER_SQFT_PER_DEG = 0.0015 # per °C below comfort floor  (COP ~3.0)
_COMFORT_CEILING_C = 26.0
_COMFORT_FLOOR_C = 18.0


@dataclass
class EnergyInputs:
    irradiance_wm2: float           # solar irradiance, W/m²
    panel_area_m2: float            # total PV array area, m²
    house_sqft: float               # conditioned floor area, sqft
    outdoor_temp_c: float           # ambient temperature, °C
    peak_sun_hours: float = 5.0     # effective full-sun hours for the day
    panel_efficiency: float = 0.20  # nameplate panel efficiency (mono-PERC default)


@dataclass
class EnergyOutputs:
    kwh_produced: float
    kwh_consumed: float
    net_kwh: float
    status: str              # "surplus" | "balanced" | "deficit"
    cell_temp_c: float
    effective_efficiency: float


def simulate_day(inputs: EnergyInputs) -> EnergyOutputs:
    # --- Solar production ---
    # Ross model: cell temperature rises above ambient based on irradiance and NOCT
    cell_temp_c = inputs.outdoor_temp_c + (_NOCT_C - 20.0) * (inputs.irradiance_wm2 / 800.0)

    # Linear temperature derating of panel efficiency
    temp_delta = cell_temp_c - _STC_TEMP_C
    effective_eff = max(0.0, inputs.panel_efficiency * (1.0 + _TEMP_COEFF * temp_delta))

    # Daily DC energy (kWh) = area × efficiency × peak_sun_hours
    # peak_sun_hours is the irradiance integral normalised to 1000 W/m²
    kwh_dc = inputs.panel_area_m2 * effective_eff * inputs.peak_sun_hours
    kwh_produced = kwh_dc * _SYSTEM_EFF

    # --- House consumption ---
    base_kwh = inputs.house_sqft * _BASE_KWH_PER_SQFT

    cooling_kwh = (
        max(0.0, inputs.outdoor_temp_c - _COMFORT_CEILING_C)
        * inputs.house_sqft
        * _COOL_KWH_PER_SQFT_PER_DEG
    )
    heating_kwh = (
        max(0.0, _COMFORT_FLOOR_C - inputs.outdoor_temp_c)
        * inputs.house_sqft
        * _HEAT_KWH_PER_SQFT_PER_DEG
    )

    kwh_consumed = base_kwh + cooling_kwh + heating_kwh

    # --- Net balance ---
    net_kwh = kwh_produced - kwh_consumed

    if net_kwh > 0.5:
        status = "surplus"
    elif net_kwh < -0.5:
        status = "deficit"
    else:
        status = "balanced"

    return EnergyOutputs(
        kwh_produced=round(kwh_produced, 3),
        kwh_consumed=round(kwh_consumed, 3),
        net_kwh=round(net_kwh, 3),
        status=status,
        cell_temp_c=round(cell_temp_c, 2),
        effective_efficiency=round(effective_eff, 4),
    )


if __name__ == "__main__":
    scenarios = [
        ("Sunny summer day — central Texas",
         EnergyInputs(irradiance_wm2=900, panel_area_m2=40,
                      house_sqft=2000, outdoor_temp_c=35, peak_sun_hours=6.5)),
        ("Mild spring day",
         EnergyInputs(irradiance_wm2=650, panel_area_m2=40,
                      house_sqft=2000, outdoor_temp_c=22, peak_sun_hours=5.5)),
        ("Overcast winter day",
         EnergyInputs(irradiance_wm2=200, panel_area_m2=40,
                      house_sqft=2000, outdoor_temp_c=5, peak_sun_hours=2.0)),
        ("Small 20-panel system (33 m²)",
         EnergyInputs(irradiance_wm2=850, panel_area_m2=33,
                      house_sqft=1800, outdoor_temp_c=28, peak_sun_hours=6.0)),
    ]

    for label, inp in scenarios:
        out = simulate_day(inp)
        print(f"=== {label} ===")
        print(f"  Produced : {out.kwh_produced:6.2f} kWh")
        print(f"  Consumed : {out.kwh_consumed:6.2f} kWh")
        print(f"  Net      : {out.net_kwh:+7.2f} kWh  [{out.status}]")
        print(f"  Cell temp: {out.cell_temp_c:.1f}°C   Eff: {out.effective_efficiency:.1%}")
        print()
