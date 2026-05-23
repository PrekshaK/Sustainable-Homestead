from enum import Enum
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import sim.models.energy_balance as eb
import sim.models.biogas as bg
import sim.models.crops as cr
import sim.models.cattle as ca
import sim.models.water as wt
from sim.models.crops import CropType

app = FastAPI(title="Homestead Simulator", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


# ── Energy balance ───────────────────────────────────────────────────────────

class EnergyRequest(BaseModel):
    irradiance_wm2: float = Field(..., gt=0, le=1400)
    panel_area_m2: float = Field(..., gt=0)
    house_sqft: float = Field(..., gt=0)
    outdoor_temp_c: float = Field(..., ge=-40, le=60)
    peak_sun_hours: float = Field(5.0, gt=0, le=14)
    panel_efficiency: float = Field(0.20, gt=0.0, lt=1.0)

    model_config = {"json_schema_extra": {"example": {
        "irradiance_wm2": 850, "panel_area_m2": 40,
        "house_sqft": 2000, "outdoor_temp_c": 30, "peak_sun_hours": 6.0,
    }}}


class EnergyResponse(BaseModel):
    kwh_produced: float
    kwh_consumed: float
    net_kwh: float
    status: str
    cell_temp_c: float
    effective_efficiency: float


@app.post("/simulate/energy", response_model=EnergyResponse)
def simulate_energy(req: EnergyRequest) -> EnergyResponse:
    r = eb.simulate_day(eb.EnergyInputs(
        irradiance_wm2=req.irradiance_wm2,
        panel_area_m2=req.panel_area_m2,
        house_sqft=req.house_sqft,
        outdoor_temp_c=req.outdoor_temp_c,
        peak_sun_hours=req.peak_sun_hours,
        panel_efficiency=req.panel_efficiency,
    ))
    return EnergyResponse(**r.__dict__)


# ── Biogas ───────────────────────────────────────────────────────────────────

class BiogasRequest(BaseModel):
    organic_waste_kg: float = Field(..., gt=0)
    temp_c: float = Field(..., ge=0, le=70)
    vs_fraction: float = Field(0.75, gt=0, lt=1)
    specific_yield_m3_per_kg_vs: float = Field(0.30, gt=0)
    retention_days: int = Field(20, ge=5, le=60)

    model_config = {"json_schema_extra": {"example": {
        "organic_waste_kg": 12, "temp_c": 35,
    }}}


class BiogasResponse(BaseModel):
    biogas_m3: float
    methane_m3: float
    kwh_equivalent: float
    vs_kg: float
    temp_correction: float


@app.post("/simulate/biogas", response_model=BiogasResponse)
def simulate_biogas(req: BiogasRequest) -> BiogasResponse:
    r = bg.simulate_day(bg.BiogasInputs(
        organic_waste_kg=req.organic_waste_kg,
        temp_c=req.temp_c,
        vs_fraction=req.vs_fraction,
        specific_yield_m3_per_kg_vs=req.specific_yield_m3_per_kg_vs,
        retention_days=req.retention_days,
    ))
    return BiogasResponse(**r.__dict__)


# ── Crops ────────────────────────────────────────────────────────────────────

class CropsRequest(BaseModel):
    crop: CropType
    land_acres: float = Field(..., gt=0)
    rainfall_mm: float = Field(..., ge=0)
    temp_max_c: float = Field(..., ge=-20, le=55)
    temp_min_c: float = Field(..., ge=-20, le=55)
    days_in_season: int = Field(..., ge=1, le=180)

    model_config = {"json_schema_extra": {"example": {
        "crop": "corn", "land_acres": 2.0,
        "rainfall_mm": 5.0, "temp_max_c": 32, "temp_min_c": 20,
        "days_in_season": 60,
    }}}


class CropsResponse(BaseModel):
    eto_mm: float
    crop_et_mm: float
    water_stress: float
    daily_yield_kg: float
    daily_kcal: float
    water_deficit_mm: float


@app.post("/simulate/crops", response_model=CropsResponse)
def simulate_crops(req: CropsRequest) -> CropsResponse:
    r = cr.simulate_day(cr.CropInputs(
        crop=req.crop,
        land_acres=req.land_acres,
        rainfall_mm=req.rainfall_mm,
        temp_max_c=req.temp_max_c,
        temp_min_c=req.temp_min_c,
        days_in_season=req.days_in_season,
    ))
    return CropsResponse(**r.__dict__)


# ── Cattle ───────────────────────────────────────────────────────────────────

class AnimalType(str, Enum):
    cow = "cow"
    goat = "goat"
    sheep = "sheep"
    chicken = "chicken"
    pig = "pig"


class CattleEntry(BaseModel):
    animal: AnimalType
    count: int = Field(..., ge=0)


class CattleRequest(BaseModel):
    herd: list[CattleEntry]

    model_config = {"json_schema_extra": {"example": {
        "herd": [{"animal": "beef", "count": 2}, {"animal": "dairy", "count": 1}],
    }}}


class CattleResponse(BaseModel):
    manure_kg_day: float
    vs_fraction: float
    vs_kg_day: float
    milk_liters_day: float
    meat_kg_day: float
    feed_required_kg_day: float
    water_liters_day: float
    kcal_day: float


@app.post("/simulate/cattle", response_model=CattleResponse)
def simulate_cattle(req: CattleRequest) -> CattleResponse:
    r = ca.simulate_day(ca.CattleInputs(
        herd=[(e.animal.value, e.count) for e in req.herd]
    ))
    return CattleResponse(**r.__dict__)


# ── Water ────────────────────────────────────────────────────────────────────

class WaterRequest(BaseModel):
    rainfall_mm: float = Field(..., ge=0)
    household_persons: int = Field(..., ge=1)
    livestock_liters_day: float = Field(0.0, ge=0)
    irrigated_area_m2: float = Field(..., ge=0)
    crop_et_mm: float = Field(..., ge=0)
    storage_liters: float = Field(..., ge=0)
    roof_area_m2: float = Field(185.0, gt=0)
    max_storage_liters: float = Field(20_000.0, gt=0)

    model_config = {"json_schema_extra": {"example": {
        "rainfall_mm": 5.0, "household_persons": 4,
        "livestock_liters_day": 170.0,
        "irrigated_area_m2": 2000, "crop_et_mm": 8.0,
        "storage_liters": 10000,
    }}}


class WaterResponse(BaseModel):
    rainfall_collected_liters: float
    household_demand_liters: float
    livestock_demand_liters: float
    irrigation_demand_liters: float
    total_demand_liters: float
    net_liters: float
    storage_liters: float
    supply_ratio: float
    status: str


@app.post("/simulate/water", response_model=WaterResponse)
def simulate_water(req: WaterRequest) -> WaterResponse:
    r = wt.simulate_day(wt.WaterInputs(
        rainfall_mm=req.rainfall_mm,
        household_persons=req.household_persons,
        livestock_liters_day=req.livestock_liters_day,
        irrigated_area_m2=req.irrigated_area_m2,
        crop_et_mm=req.crop_et_mm,
        storage_liters=req.storage_liters,
        roof_area_m2=req.roof_area_m2,
        max_storage_liters=req.max_storage_liters,
    ))
    return WaterResponse(**r.__dict__)


# ── Full day (all models, cattle → biogas chain wired automatically) ──────────

class WeatherBlock(BaseModel):
    irradiance_wm2: float = Field(..., gt=0, le=1400)
    outdoor_temp_c: float = Field(..., ge=-40, le=60)
    temp_max_c: float = Field(..., ge=-20, le=55)
    temp_min_c: float = Field(..., ge=-20, le=55)
    rainfall_mm: float = Field(..., ge=0)
    peak_sun_hours: float = Field(5.0, gt=0, le=14)


class SolarBlock(BaseModel):
    panel_area_m2: float = Field(..., gt=0)
    house_sqft: float = Field(..., gt=0)
    panel_efficiency: float = Field(0.20, gt=0, lt=1)


class DigestorBlock(BaseModel):
    digester_temp_c: float = Field(35.0, ge=0, le=70)
    retention_days: int = Field(20, ge=5, le=60)


class CropsBlock(BaseModel):
    crop: CropType
    land_acres: float = Field(..., gt=0)
    days_in_season: int = Field(..., ge=1, le=180)


class WaterBlock(BaseModel):
    household_persons: int = Field(..., ge=1)
    irrigated_area_m2: float = Field(..., ge=0)
    storage_liters: float = Field(..., ge=0)
    max_storage_liters: float = Field(20_000.0, gt=0)


class FullDayRequest(BaseModel):
    weather: WeatherBlock
    solar: SolarBlock
    digestor: DigestorBlock = DigestorBlock()
    crops: list[CropsBlock]
    cattle: list[CattleEntry]
    water: WaterBlock

    model_config = {"json_schema_extra": {"example": {
        "weather": {"irradiance_wm2": 850, "outdoor_temp_c": 30,
                    "temp_max_c": 35, "temp_min_c": 25,
                    "rainfall_mm": 3.0, "peak_sun_hours": 6.0},
        "solar": {"panel_area_m2": 40, "house_sqft": 2000},
        "crops": [{"crop": "corn", "land_acres": 2.0, "days_in_season": 60}],
        "cattle": [{"animal": "beef", "count": 2}, {"animal": "dairy", "count": 1}],
        "water": {"household_persons": 4, "irrigated_area_m2": 2000,
                  "storage_liters": 10000},
    }}}


class SummaryBlock(BaseModel):
    total_kwh_produced: float   # solar + biogas
    total_kwh_consumed: float
    net_kwh: float
    total_food_kcal: float      # crops + cattle
    water_status: str
    water_supply_ratio: float


class FullDayResponse(BaseModel):
    energy: EnergyResponse
    biogas: BiogasResponse
    crops: CropsResponse
    cattle: CattleResponse
    water: WaterResponse
    summary: SummaryBlock


@app.post("/simulate/full", response_model=FullDayResponse)
def simulate_full(req: FullDayRequest) -> FullDayResponse:
    w = req.weather

    # Energy
    energy = eb.simulate_day(eb.EnergyInputs(
        irradiance_wm2=w.irradiance_wm2,
        panel_area_m2=req.solar.panel_area_m2,
        house_sqft=req.solar.house_sqft,
        outdoor_temp_c=w.outdoor_temp_c,
        peak_sun_hours=w.peak_sun_hours,
        panel_efficiency=req.solar.panel_efficiency,
    ))

    # Cattle first — its manure feeds biogas
    cattle = ca.simulate_day(ca.CattleInputs(
        herd=[(e.animal.value, e.count) for e in req.cattle]
    ))

    # Biogas — wired from cattle output automatically
    biogas = bg.simulate_day(bg.BiogasInputs(
        organic_waste_kg=cattle.manure_kg_day,
        temp_c=req.digestor.digester_temp_c,
        vs_fraction=cattle.vs_fraction,
        specific_yield_m3_per_kg_vs=0.22,   # cattle-specific yield
        retention_days=req.digestor.retention_days,
    ))

    # Crops — simulate each then aggregate (area-weighted averages, summed totals)
    crop_results = [
        cr.simulate_day(cr.CropInputs(
            crop=c.crop,
            land_acres=c.land_acres,
            rainfall_mm=w.rainfall_mm,
            temp_max_c=w.temp_max_c,
            temp_min_c=w.temp_min_c,
            days_in_season=c.days_in_season,
        ))
        for c in req.crops
    ]
    total_acres = sum(c.land_acres for c in req.crops)

    def _wavg(field: str) -> float:
        return sum(getattr(r, field) * c.land_acres for r, c in zip(crop_results, req.crops)) / total_acres

    from sim.models.crops import CropOutputs
    crops = CropOutputs(
        eto_mm=round(_wavg('eto_mm'), 3),
        crop_et_mm=round(_wavg('crop_et_mm'), 3),
        water_stress=round(_wavg('water_stress'), 4),
        daily_yield_kg=round(sum(r.daily_yield_kg for r in crop_results), 3),
        daily_kcal=round(sum(r.daily_kcal for r in crop_results), 1),
        water_deficit_mm=round(_wavg('water_deficit_mm'), 3),
    )

    # Water — crop_et_mm wired from crops output automatically
    water = wt.simulate_day(wt.WaterInputs(
        rainfall_mm=w.rainfall_mm,
        household_persons=req.water.household_persons,
        livestock_liters_day=cattle.water_liters_day,
        irrigated_area_m2=req.water.irrigated_area_m2,
        crop_et_mm=crops.crop_et_mm,
        storage_liters=req.water.storage_liters,
        max_storage_liters=req.water.max_storage_liters,
    ))

    summary = SummaryBlock(
        total_kwh_produced=round(energy.kwh_produced + biogas.kwh_equivalent, 3),
        total_kwh_consumed=round(energy.kwh_consumed, 3),
        net_kwh=round(energy.kwh_produced + biogas.kwh_equivalent - energy.kwh_consumed, 3),
        total_food_kcal=round(crops.daily_kcal + cattle.kcal_day, 1),
        water_status=water.status,
        water_supply_ratio=water.supply_ratio,
    )

    return FullDayResponse(
        energy=EnergyResponse(**energy.__dict__),
        biogas=BiogasResponse(**biogas.__dict__),
        crops=CropsResponse(**crops.__dict__),
        cattle=CattleResponse(**cattle.__dict__),
        water=WaterResponse(**water.__dict__),
        summary=summary,
    )
