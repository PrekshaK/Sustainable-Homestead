import { NetGauge } from './charts/NetGauge'

const STATUS_COLORS = {
  surplus:    'text-green-400  bg-green-400/10  border-green-400/20',
  balanced:   'text-yellow-400 bg-yellow-400/10 border-yellow-400/20',
  deficit:    'text-red-400    bg-red-400/10    border-red-400/20',
  sufficient: 'text-green-400  bg-green-400/10  border-green-400/20',
  stressed:   'text-yellow-400 bg-yellow-400/10 border-yellow-400/20',
  critical:   'text-red-400    bg-red-400/10    border-red-400/20',
}

function StatusBadge({ status }) {
  const cls = STATUS_COLORS[status] ?? 'text-gray-400 bg-gray-400/10 border-gray-400/20'
  return (
    <span className={`inline-block px-2 py-0.5 rounded border text-xs font-bold uppercase tracking-wide ${cls}`}>
      {status}
    </span>
  )
}

function Card({ title, accent, children }) {
  const titleColor = {
    yellow: 'text-yellow-400', purple: 'text-purple-400',
    orange: 'text-orange-400', blue: 'text-blue-400',
  }[accent] ?? 'text-gray-400'
  return (
    <div className="bg-gray-800/60 rounded-2xl p-5 border border-gray-700/50">
      <h3 className={`text-xs font-bold uppercase tracking-widest mb-4 ${titleColor}`}>{title}</h3>
      {children}
    </div>
  )
}

function Metric({ label, value, unit = '', color = 'text-white' }) {
  return (
    <div className="flex justify-between items-baseline py-1">
      <span className="text-sm text-gray-400">{label}</span>
      <span className={`text-sm font-mono font-semibold tabular-nums ${color}`}>
        {value}
        {unit && <span className="text-gray-500 text-xs ml-1">{unit}</span>}
      </span>
    </div>
  )
}

function Divider() {
  return <div className="border-t border-gray-700 my-2" />
}

function ProgressBar({ ratio }) {
  const pct = Math.min(100, Math.max(0, ratio * 100))
  const bg = ratio >= 0.7 ? '#22c55e' : ratio >= 0.3 ? '#eab308' : '#ef4444'
  return (
    <div className="w-full bg-gray-700 rounded-full h-2.5 mt-1.5 mb-2">
      <div
        className="h-2.5 rounded-full transition-all duration-500"
        style={{ width: `${pct.toFixed(1)}%`, backgroundColor: bg }}
      />
    </div>
  )
}

function fmt(n, decimals = 1) {
  return n.toLocaleString(undefined, { maximumFractionDigits: decimals, minimumFractionDigits: decimals })
}

function fmtInt(n) {
  return Math.round(n).toLocaleString()
}

export function Dashboard({ result, loading, error }) {
  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-red-400 text-sm bg-red-400/10 rounded-xl p-6 border border-red-400/20 max-w-md">
          <p className="font-semibold mb-1">API error</p>
          <p className="text-gray-400 text-xs">{error}</p>
          <p className="text-gray-500 text-xs mt-3">Make sure the FastAPI server is running: <code className="bg-gray-800 px-1 rounded">uvicorn sim.main:app --reload</code></p>
        </div>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-gray-600 text-sm">Connecting to simulator...</p>
      </div>
    )
  }

  const { energy, biogas, crops, cattle, water, summary } = result
  const netStatus = summary.net_kwh > 0.5 ? 'surplus' : summary.net_kwh < -0.5 ? 'deficit' : 'balanced'

  return (
    <div className={`transition-opacity duration-150 ${loading ? 'opacity-50' : 'opacity-100'}`}>

      {/* Summary header */}
      <div className="flex items-center gap-6 mb-5 bg-gray-800/40 rounded-2xl p-5 border border-gray-700/50">
        <NetGauge net={summary.net_kwh} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-3">
            <h2 className="text-base font-bold text-white">Day Summary</h2>
            <StatusBadge status={netStatus} />
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide mb-0.5">Produced</p>
              <p className="text-2xl font-mono font-bold text-green-400 leading-none">
                {fmt(summary.total_kwh_produced)}
              </p>
              <p className="text-xs text-gray-500 mt-0.5">kWh  solar + biogas</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide mb-0.5">Consumed</p>
              <p className="text-2xl font-mono font-bold text-red-400 leading-none">
                {fmt(summary.total_kwh_consumed)}
              </p>
              <p className="text-xs text-gray-500 mt-0.5">kWh  house load</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide mb-0.5">Food</p>
              <p className="text-2xl font-mono font-bold text-orange-400 leading-none">
                {(summary.total_food_kcal / 1000).toFixed(1)}k
              </p>
              <p className="text-xs text-gray-500 mt-0.5">kcal/day  crops + cattle</p>
            </div>
          </div>
        </div>
      </div>

      {/* 2×2 cards */}
      <div className="grid grid-cols-2 gap-4">

        {/* Solar */}
        <Card title="Solar Energy" accent="yellow">
          <Metric label="Produced" value={fmt(energy.kwh_produced)} unit="kWh" color="text-yellow-400" />
          <Metric label="Consumed" value={fmt(energy.kwh_consumed)} unit="kWh" color="text-red-400" />
          <Metric
            label="Net (solar only)"
            value={energy.net_kwh >= 0 ? `+${fmt(energy.net_kwh)}` : fmt(energy.net_kwh)}
            unit="kWh"
            color={energy.net_kwh >= 0 ? 'text-green-400' : 'text-red-400'}
          />
          <Divider />
          <Metric label="Cell temperature" value={fmt(energy.cell_temp_c)} unit="°C" />
          <Metric label="Panel efficiency" value={fmt(energy.effective_efficiency * 100)} unit="%" />
        </Card>

        {/* Biogas */}
        <Card title="Biogas Digester" accent="purple">
          <Metric label="Energy output" value={fmt(biogas.kwh_equivalent)} unit="kWh" color="text-purple-400" />
          <Metric label="Raw biogas" value={fmt(biogas.biogas_m3)} unit="m³/day" />
          <Metric label="Methane" value={fmt(biogas.methane_m3)} unit="m³/day" />
          <Divider />
          <Metric label="VS fed today" value={fmt(biogas.vs_kg)} unit="kg" />
          <Metric label="Temp factor" value={biogas.temp_correction.toFixed(3)} />
        </Card>

        {/* Food */}
        <Card title="Food Production" accent="orange">
          <Metric
            label="Total calories"
            value={fmtInt(summary.total_food_kcal)}
            unit="kcal/day"
            color="text-orange-400"
          />
          <Divider />
          <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Crops</p>
          <Metric label="Yield" value={fmt(crops.daily_yield_kg)} unit="kg/day" />
          <Metric label="Calories" value={fmtInt(crops.daily_kcal)} unit="kcal" />
          <Metric
            label="Water stress"
            value={fmt(crops.water_stress * 100, 0)}
            unit="%"
            color={crops.water_stress >= 0.7 ? 'text-green-400' : crops.water_stress >= 0.3 ? 'text-yellow-400' : 'text-red-400'}
          />
          <Divider />
          <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Cattle</p>
          <Metric label="Milk" value={fmt(cattle.milk_liters_day)} unit="L/day" />
          <Metric label="Meat equiv." value={fmt(cattle.meat_kg_day)} unit="kg/day" />
        </Card>

        {/* Water */}
        <Card title="Water Cycle" accent="blue">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">Supply ratio</span>
            <div className="flex items-center gap-2">
              <span className="text-sm font-mono font-bold text-white">
                {fmt(water.supply_ratio * 100, 0)}%
              </span>
              <StatusBadge status={water.status} />
            </div>
          </div>
          <ProgressBar ratio={water.supply_ratio} />
          <Divider />
          <Metric label="Collected" value={fmtInt(water.rainfall_collected_liters)} unit="L" color="text-blue-400" />
          <Metric label="Household demand" value={fmtInt(water.household_demand_liters)} unit="L" />
          <Metric label="Livestock demand" value={fmtInt(water.livestock_demand_liters)} unit="L" />
          <Metric label="Irrigation demand" value={fmtInt(water.irrigation_demand_liters)} unit="L" />
          <Divider />
          <Metric label="Tank end-of-day" value={fmtInt(water.storage_liters)} unit="L" />
        </Card>

      </div>
    </div>
  )
}
