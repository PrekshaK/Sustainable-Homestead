export const DEFAULT_INPUTS = {
  weather: {
    irradiance_wm2: 850,
    temp_max_c: 35,
    temp_min_c: 25,
    rainfall_mm: 3,
    peak_sun_hours: 6,
  },
  solar: {
    panel_area_m2: 40,
    house_sqft: 2000,
  },
  crops: [
    { crop: 'corn', land_acres: 2, days_in_season: 60 },
  ],
  cattle: [
    { animal: 'cow', count: 2 },
  ],
  water: {
    household_persons: 4,
    irrigated_area_m2: 2000,
    storage_liters: 10000,
  },
}

export function buildRequest(inputs) {
  const outdoor_temp_c = (inputs.weather.temp_max_c + inputs.weather.temp_min_c) / 2
  return {
    weather: {
      irradiance_wm2: inputs.weather.irradiance_wm2,
      outdoor_temp_c,
      temp_max_c: inputs.weather.temp_max_c,
      temp_min_c: inputs.weather.temp_min_c,
      rainfall_mm: inputs.weather.rainfall_mm,
      peak_sun_hours: inputs.weather.peak_sun_hours,
    },
    solar: {
      panel_area_m2: inputs.solar.panel_area_m2,
      house_sqft: inputs.solar.house_sqft,
      panel_efficiency: 0.20,
    },
    crops: inputs.crops,
    cattle: inputs.cattle,
    water: inputs.water,
  }
}
