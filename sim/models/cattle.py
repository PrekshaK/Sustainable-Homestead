from dataclasses import dataclass
from typing import List, Tuple

_MILK_KCAL_PER_LITER = 610.0

# Per-species biophysical constants
# bw: average body weight (kg), manure: manure fraction of BW/day,
# vs: volatile solids fraction of wet manure, dmi: dry matter intake fraction of BW,
# milk: milk output (L/day/animal), slaughter: slaughter live weight (kg),
# dress: dressing percentage, turnover: slaughter cycles/year,
# meat_kcal: kcal/kg carcass, egg_kcal: kcal/animal/day from eggs, water_L: water demand (L/day)
_SP: dict = {
    'cow':     dict(bw=500, manure=0.054, vs=0.10, dmi=0.025, milk=0,    slaughter=500, dress=0.60, turnover=1.0, meat_kcal=2500, egg_kcal=0,  water_L=40),
    'goat':    dict(bw=60,  manure=0.050, vs=0.10, dmi=0.030, milk=2.0,  slaughter=30,  dress=0.48, turnover=1.0, meat_kcal=1090, egg_kcal=0,  water_L=8),
    'sheep':   dict(bw=70,  manure=0.045, vs=0.10, dmi=0.025, milk=0.5,  slaughter=35,  dress=0.50, turnover=1.0, meat_kcal=1422, egg_kcal=0,  water_L=5),
    'chicken': dict(bw=1.8, manure=0.072, vs=0.15, dmi=0.030, milk=0,    slaughter=2.0, dress=0.72, turnover=2.0, meat_kcal=1650, egg_kcal=70, water_L=0.3),
    'pig':     dict(bw=100, manure=0.050, vs=0.12, dmi=0.030, milk=0,    slaughter=100, dress=0.72, turnover=2.5, meat_kcal=2750, egg_kcal=0,  water_L=15),
}


@dataclass
class CattleInputs:
    herd: List[Tuple[str, int]]  # list of (species, count)


@dataclass
class CattleOutputs:
    manure_kg_day: float
    vs_fraction: float       # weighted average across all species
    vs_kg_day: float
    milk_liters_day: float
    meat_kg_day: float
    feed_required_kg_day: float
    water_liters_day: float
    kcal_day: float


def simulate_day(inputs: CattleInputs) -> CattleOutputs:
    manure_kg_day = 0.0
    vs_kg_day = 0.0
    feed_kg_day = 0.0
    milk_L_day = 0.0
    meat_kg_day = 0.0
    meat_kcal_day = 0.0
    egg_kcal_day = 0.0
    water_L_day = 0.0

    for species, count in inputs.herd:
        if count == 0:
            continue
        sp = _SP[species]
        bw = sp['bw']
        manure = count * bw * sp['manure']
        manure_kg_day += manure
        vs_kg_day += manure * sp['vs']
        feed_kg_day += count * bw * sp['dmi']
        milk_L_day += count * sp['milk']
        animal_meat = count * sp['slaughter'] * sp['dress'] * sp['turnover'] / 365.0
        meat_kg_day += animal_meat
        meat_kcal_day += animal_meat * sp['meat_kcal']
        egg_kcal_day += count * sp['egg_kcal']
        water_L_day += count * sp['water_L']

    avg_vs = vs_kg_day / manure_kg_day if manure_kg_day > 0 else 0.10
    kcal_day = milk_L_day * _MILK_KCAL_PER_LITER + meat_kcal_day + egg_kcal_day

    return CattleOutputs(
        manure_kg_day=round(manure_kg_day, 3),
        vs_fraction=round(avg_vs, 4),
        vs_kg_day=round(vs_kg_day, 3),
        milk_liters_day=round(milk_L_day, 2),
        meat_kg_day=round(meat_kg_day, 3),
        feed_required_kg_day=round(feed_kg_day, 2),
        water_liters_day=round(water_L_day, 1),
        kcal_day=round(kcal_day, 1),
    )