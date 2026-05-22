from dataclasses import dataclass

# Manure output as fraction of body weight (wet basis)
_MANURE_FRAC_OF_BW = 0.054        # ~5.4% BW/day; USDA-NRCS value for beef cattle
_DAIRY_MANURE_FRAC_OF_BW = 0.092  # dairy cows produce more due to higher feed intake

# Volatile solids as fraction of wet manure mass
# Cattle manure VS fraction: ~10% (wet basis); differs from "mixed organics" default in biogas.py
CATTLE_VS_FRACTION = 0.10

# Methane yield for cattle manure (m³ CH4 / kg VS) — lower than mixed organics
# Use this when wiring cattle → biogas instead of biogas.py default (0.30)
CATTLE_SPECIFIC_YIELD_M3_PER_KG_VS = 0.22

# Dry matter intake as fraction of body weight
_DMI_FRAC = 0.025

# Dairy production
_MILK_LITERS_PER_COW_DAY = 22.0   # modest homestead herd (Holstein avg is ~30L, grazed lower)
_MILK_KCAL_PER_LITER = 610.0

# Meat: dressing percentage (carcass / live weight)
_DRESSING_PCT = 0.60

# Caloric density of beef carcass (kcal / kg)
_BEEF_KCAL_PER_KG = 2500.0


@dataclass
class CattleInputs:
    beef_head: int                       # number of beef cattle
    dairy_cows: int                      # number of dairy cows
    avg_beef_weight_kg: float = 500.0    # average live weight, beef
    avg_dairy_weight_kg: float = 600.0   # average live weight, dairy
    slaughter_weight_kg: float = 500.0   # target live weight at slaughter
    turnover_rate: float = 1.0           # slaughter cycles per year (1 = annual)


@dataclass
class CattleOutputs:
    # Biogas feedstock — wire directly to BiogasInputs
    manure_kg_day: float        # total wet manure (organic_waste_kg for biogas)
    vs_fraction: float          # volatile solids fraction (use instead of biogas default)
    vs_kg_day: float            # volatile solids mass (convenience)

    # Food outputs
    milk_liters_day: float      # daily milk from dairy cows
    meat_kg_day: float          # annualised daily meat equivalent (carcass weight)

    # Resource demand
    feed_required_kg_day: float # total dry matter intake

    # Energy summary
    kcal_day: float             # total food calories (milk + meat equivalent)


def simulate_day(inputs: CattleInputs) -> CattleOutputs:
    # --- Manure production ---
    beef_manure_kg = (
        inputs.beef_head * inputs.avg_beef_weight_kg * _MANURE_FRAC_OF_BW
    )
    dairy_manure_kg = (
        inputs.dairy_cows * inputs.avg_dairy_weight_kg * _DAIRY_MANURE_FRAC_OF_BW
    )
    manure_kg_day = beef_manure_kg + dairy_manure_kg
    vs_kg_day = manure_kg_day * CATTLE_VS_FRACTION

    # --- Feed demand ---
    feed_required_kg_day = (
        inputs.beef_head * inputs.avg_beef_weight_kg * _DMI_FRAC
        + inputs.dairy_cows * inputs.avg_dairy_weight_kg * _DMI_FRAC
    )

    # --- Dairy output ---
    milk_liters_day = inputs.dairy_cows * _MILK_LITERS_PER_COW_DAY

    # --- Meat output (annualised to a daily rate) ---
    # Each beef animal reaches slaughter weight once per turnover_rate years
    carcass_kg_per_animal = inputs.slaughter_weight_kg * _DRESSING_PCT
    meat_kg_day = (
        inputs.beef_head * carcass_kg_per_animal * inputs.turnover_rate / 365.0
    )

    # --- Caloric summary ---
    milk_kcal = milk_liters_day * _MILK_KCAL_PER_LITER
    meat_kcal = meat_kg_day * _BEEF_KCAL_PER_KG
    kcal_day = milk_kcal + meat_kcal

    return CattleOutputs(
        manure_kg_day=round(manure_kg_day, 3),
        vs_fraction=CATTLE_VS_FRACTION,
        vs_kg_day=round(vs_kg_day, 3),
        milk_liters_day=round(milk_liters_day, 2),
        meat_kg_day=round(meat_kg_day, 3),
        feed_required_kg_day=round(feed_required_kg_day, 2),
        kcal_day=round(kcal_day, 1),
    )


if __name__ == "__main__":
    from sim.models.biogas import BiogasInputs, simulate_day as biogas_day

    scenarios = [
        ("Minimal homestead — 2 beef, 1 dairy",
         CattleInputs(beef_head=2, dairy_cows=1)),
        ("Mid-size — 5 beef, 2 dairy",
         CattleInputs(beef_head=5, dairy_cows=2)),
        ("Dairy-focused — 0 beef, 4 dairy",
         CattleInputs(beef_head=0, dairy_cows=4)),
        ("Meat-only — 10 beef, 0 dairy",
         CattleInputs(beef_head=10, dairy_cows=0, avg_beef_weight_kg=450)),
    ]

    for label, inp in scenarios:
        out = simulate_day(inp)
        print(f"=== {label} ===")
        print(f"  Manure        : {out.manure_kg_day:.1f} kg/day  (VS: {out.vs_kg_day:.2f} kg)")
        print(f"  Milk          : {out.milk_liters_day:.1f} L/day")
        print(f"  Meat equiv.   : {out.meat_kg_day:.3f} kg/day  ({out.meat_kg_day * 365:.0f} kg/year)")
        print(f"  Feed needed   : {out.feed_required_kg_day:.1f} kg DM/day")
        print(f"  Food energy   : {out.kcal_day:,.0f} kcal/day")

        # Wire into biogas to show the chain
        bg = biogas_day(BiogasInputs(
            organic_waste_kg=out.manure_kg_day,
            temp_c=35,
            vs_fraction=out.vs_fraction,
            specific_yield_m3_per_kg_vs=0.22,
        ))
        print(f"  → Biogas      : {bg.biogas_m3:.2f} m³/day  ({bg.kwh_equivalent:.1f} kWh)")
        print()
