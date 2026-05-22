from dataclasses import dataclass

# Mesophilic digestion reference temperature (°C)
_T_REF_C = 35.0
# Arrhenius-style temperature correction base for mesophilic bacteria
_THETA = 1.04
# Methane fraction in raw biogas (volumetric)
_CH4_FRACTION = 0.60
# Energy content of methane (kWh per m³ at STP)
_CH4_KWH_PER_M3 = 10.0
# Generator/CHP conversion efficiency (biogas → usable heat+electricity)
_CONVERSION_EFF = 0.80


@dataclass
class BiogasInputs:
    organic_waste_kg: float      # total wet organic waste fed per day (kg)
    temp_c: float                # digester temperature (°C)
    vs_fraction: float = 0.75   # volatile solids as fraction of wet mass
    specific_yield_m3_per_kg_vs: float = 0.30  # m³ CH4 per kg VS (mixed organics default)
    retention_days: int = 20    # hydraulic retention time (days)


@dataclass
class BiogasOutputs:
    biogas_m3: float        # total raw biogas produced per day
    methane_m3: float       # methane fraction per day
    kwh_equivalent: float   # usable energy from biogas (kWh)
    vs_kg: float            # volatile solids fed today
    temp_correction: float  # dimensionless temperature correction factor


def simulate_day(inputs: BiogasInputs) -> BiogasOutputs:
    # --- Volatile solids load ---
    vs_kg = inputs.organic_waste_kg * inputs.vs_fraction

    # Temperature correction: microbial activity relative to T_ref
    # Using modified Arrhenius; clamp to avoid negative rates in extreme cold
    temp_correction = max(0.0, _THETA ** (inputs.temp_c - _T_REF_C))

    # --- Methane production ---
    # HRT dampens daily yield: short retention = incomplete digestion
    # Simple first-order approximation: fraction digested = 1 - e^(-k * HRT)
    # k ≈ 0.1/day at mesophilic temps (Chen & Hashimoto model simplified)
    k = 0.10 * temp_correction
    digestion_fraction = 1.0 - 2.718281828 ** (-k * inputs.retention_days)
    digestion_fraction = min(digestion_fraction, 1.0)

    methane_m3 = vs_kg * inputs.specific_yield_m3_per_kg_vs * digestion_fraction

    # --- Biogas and energy ---
    biogas_m3 = methane_m3 / _CH4_FRACTION
    kwh_equivalent = methane_m3 * _CH4_KWH_PER_M3 * _CONVERSION_EFF

    return BiogasOutputs(
        biogas_m3=round(biogas_m3, 3),
        methane_m3=round(methane_m3, 3),
        kwh_equivalent=round(kwh_equivalent, 3),
        vs_kg=round(vs_kg, 3),
        temp_correction=round(temp_correction, 4),
    )


if __name__ == "__main__":
    scenarios = [
        ("Small homestead — 4 people, mesophilic",
         BiogasInputs(organic_waste_kg=12, temp_c=35)),
        ("Cold digester — winter Texas (15°C)",
         BiogasInputs(organic_waste_kg=12, temp_c=15)),
        ("Large farm — 50 kg/day waste, 37°C",
         BiogasInputs(organic_waste_kg=50, temp_c=37, vs_fraction=0.80)),
        ("Short retention (10 days)",
         BiogasInputs(organic_waste_kg=12, temp_c=35, retention_days=10)),
    ]

    for label, inp in scenarios:
        out = simulate_day(inp)
        print(f"=== {label} ===")
        print(f"  VS fed        : {out.vs_kg:.2f} kg")
        print(f"  Temp factor   : {out.temp_correction:.3f}")
        print(f"  Biogas        : {out.biogas_m3:.3f} m³/day")
        print(f"  Methane       : {out.methane_m3:.3f} m³/day")
        print(f"  Usable energy : {out.kwh_equivalent:.2f} kWh")
        print()
