const CROP_OPTIONS = ['corn', 'tomato', 'potato', 'beans', 'wheat']
const ANIMAL_OPTIONS = ['cow', 'goat', 'sheep', 'chicken', 'pig']

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

export function ScenarioPanel({ inputs, setInput, setCropField, addCrop, removeCrop, setCattleField, addCattle, removeCattle }) {
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
        {inputs.crops.map((crop, i) => (
          <div key={i} className="mb-4 border border-gray-700/60 rounded-xl p-3">
            <div className="flex justify-between items-center mb-3">
              <span className="text-xs font-semibold text-gray-300 uppercase tracking-wide">
                Crop {i + 1}
              </span>
              {inputs.crops.length > 1 && (
                <button
                  onClick={() => removeCrop(i)}
                  className="text-xs text-red-400 hover:text-red-300 transition-colors"
                >
                  Remove
                </button>
              )}
            </div>
            <div className="mb-3">
              <span className="text-sm text-gray-400 block mb-1.5">Type</span>
              <select
                value={crop.crop}
                onChange={e => setCropField(i, 'crop', e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-green-500 cursor-pointer"
              >
                {CROP_OPTIONS.map(c => (
                  <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
                ))}
              </select>
            </div>
            <SliderField label="Land area" value={crop.land_acres}
              min={0.5} max={20} step={0.5} unit="acres"
              onChange={v => setCropField(i, 'land_acres', v)} />
            <SliderField label="Days in season" value={crop.days_in_season}
              min={1} max={150} step={1} unit="days"
              onChange={v => setCropField(i, 'days_in_season', v)} />
          </div>
        ))}
        <button
          onClick={addCrop}
          className="w-full py-2 text-sm text-green-400 border border-dashed border-green-400/40 rounded-lg hover:bg-green-400/5 transition-colors"
        >
          + Add crop
        </button>
      </Section>

      <Section title="Livestock">
        {inputs.cattle.map((entry, i) => (
          <div key={i} className="mb-4 border border-gray-700/60 rounded-xl p-3">
            <div className="flex justify-between items-center mb-3">
              <span className="text-xs font-semibold text-gray-300 uppercase tracking-wide">
                Livestock {i + 1}
              </span>
              {inputs.cattle.length > 1 && (
                <button
                  onClick={() => removeCattle(i)}
                  className="text-xs text-red-400 hover:text-red-300 transition-colors"
                >
                  Remove
                </button>
              )}
            </div>
            <div className="mb-3">
              <span className="text-sm text-gray-400 block mb-1.5">Species</span>
              <select
                value={entry.animal}
                onChange={e => setCattleField(i, 'animal', e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-green-500 cursor-pointer"
              >
                {ANIMAL_OPTIONS.map(a => (
                  <option key={a} value={a}>{a.charAt(0).toUpperCase() + a.slice(1)}</option>
                ))}
              </select>
            </div>
            <SliderField label="Count" value={entry.count}
              min={0} max={50} step={1} unit="head"
              onChange={v => setCattleField(i, 'count', v)} />
          </div>
        ))}
        <button
          onClick={addCattle}
          className="w-full py-2 text-sm text-green-400 border border-dashed border-green-400/40 rounded-lg hover:bg-green-400/5 transition-colors"
        >
          + Add livestock
        </button>
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
