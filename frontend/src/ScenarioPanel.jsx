const CROP_OPTIONS = ['corn', 'tomato', 'potato', 'beans', 'wheat']

function SliderField({ label, value, min, max, step = 1, unit = '', onChange }) {
  return (
    <div className="mb-4">
      <div className="flex justify-between items-baseline mb-1.5">
        <span className="text-sm text-gray-400">{label}</span>
        <span className="text-sm font-mono text-white tabular-nums">
          {value.toLocaleString()}
          {unit && <span className="text-gray-500 text-xs ml-1">{unit}</span>}
        </span>
      </div>
      <input
        type="range"
        min={min} max={max} step={step} value={value}
        onChange={e => onChange(Number(e.target.value))}
      />
    </div>
  )
}

function Section({ title, children }) {
  return (
    <div className="mb-6">
      <h3 className="text-xs font-bold uppercase tracking-widest text-gray-500 mb-3 border-b border-gray-800 pb-1">
        {title}
      </h3>
      {children}
    </div>
  )
}

export function ScenarioPanel({ inputs, setInput }) {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-base font-bold text-white">Homestead Simulator</h1>
        <p className="text-xs text-gray-500 mt-0.5">One-day scenario</p>
      </div>

      <Section title="Weather">
        <SliderField label="Solar irradiance" value={inputs.weather.irradiance_wm2}
          min={0} max={1200} step={10} unit="W/m²"
          onChange={v => setInput('weather', 'irradiance_wm2', v)} />
        <SliderField label="Temp max" value={inputs.weather.temp_max_c}
          min={-10} max={50} step={1} unit="°C"
          onChange={v => setInput('weather', 'temp_max_c', v)} />
        <SliderField label="Temp min" value={inputs.weather.temp_min_c}
          min={-20} max={40} step={1} unit="°C"
          onChange={v => setInput('weather', 'temp_min_c', v)} />
        <SliderField label="Rainfall" value={inputs.weather.rainfall_mm}
          min={0} max={100} step={0.5} unit="mm"
          onChange={v => setInput('weather', 'rainfall_mm', v)} />
        <SliderField label="Peak sun hours" value={inputs.weather.peak_sun_hours}
          min={1} max={12} step={0.5} unit="hrs"
          onChange={v => setInput('weather', 'peak_sun_hours', v)} />
      </Section>

      <Section title="Solar System">
        <SliderField label="Panel area" value={inputs.solar.panel_area_m2}
          min={10} max={120} step={5} unit="m²"
          onChange={v => setInput('solar', 'panel_area_m2', v)} />
        <SliderField label="House size" value={inputs.solar.house_sqft}
          min={500} max={5000} step={100} unit="sqft"
          onChange={v => setInput('solar', 'house_sqft', v)} />
      </Section>

      <Section title="Crops">
        <div className="mb-4">
          <span className="text-sm text-gray-400 block mb-1.5">Crop type</span>
          <select
            value={inputs.crops.crop}
            onChange={e => setInput('crops', 'crop', e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-green-500 cursor-pointer"
          >
            {CROP_OPTIONS.map(c => (
              <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
            ))}
          </select>
        </div>
        <SliderField label="Land area" value={inputs.crops.land_acres}
          min={0.5} max={20} step={0.5} unit="acres"
          onChange={v => setInput('crops', 'land_acres', v)} />
        <SliderField label="Days in season" value={inputs.crops.days_in_season}
          min={1} max={150} step={1} unit="days"
          onChange={v => setInput('crops', 'days_in_season', v)} />
      </Section>

      <Section title="Cattle">
        <SliderField label="Beef cattle" value={inputs.cattle.beef_head}
          min={0} max={30} step={1} unit="head"
          onChange={v => setInput('cattle', 'beef_head', v)} />
        <SliderField label="Dairy cows" value={inputs.cattle.dairy_cows}
          min={0} max={15} step={1} unit="cows"
          onChange={v => setInput('cattle', 'dairy_cows', v)} />
      </Section>

      <Section title="Water">
        <SliderField label="Household" value={inputs.water.household_persons}
          min={1} max={12} step={1} unit="people"
          onChange={v => setInput('water', 'household_persons', v)} />
        <SliderField label="Irrigated area" value={inputs.water.irrigated_area_m2}
          min={0} max={10000} step={100} unit="m²"
          onChange={v => setInput('water', 'irrigated_area_m2', v)} />
        <SliderField label="Tank storage" value={inputs.water.storage_liters}
          min={0} max={50000} step={500} unit="L"
          onChange={v => setInput('water', 'storage_liters', v)} />
      </Section>
    </div>
  )
}
