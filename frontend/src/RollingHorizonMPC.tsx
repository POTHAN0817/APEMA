import { useState, useEffect } from 'react'
import Plot from 'react-plotly.js'

interface RollingOptimizationResponse {
  simulation_status: string
  mode: string
  total_grid_cost: number
  total_grid_cost_inr: number
  total_battery_throughput: number
  battery_throughput_kwh: number
  estimated_degradation_cost: number
  degradation_cost_inr: number
  final_soc: number
  final_soc_percent: number
  results_file: string
  number_of_iterations: number
  iterations_completed: number
}

interface RollingRow {
  step: number
  timestamp: string
  predicted_demand_kw: number
  actual_demand_kw: number
  solar_generation_kw: number
  tariff_inr_per_kwh: number
  grid_import_kw: number
  battery_charge_kw: number
  battery_discharge_kw: number
  battery_energy_kwh: number
  battery_soc: number
  solar_used_kw: number
  solar_curtailment_kw: number
  grid_cost_inr: number
  battery_throughput_kwh: number
  degradation_cost_inr: number
  soc_before: number
  soc_after: number
}

interface ComparisonRow {
  strategy: string
  display_name: string
  strategy_type: string
  grid_cost_inr: number
  battery_throughput_kwh: number
  degradation_cost_inr: number
  final_soc_percent: number
  runtime_seconds: number
}

interface RollingHorizonMPCProps {
  apiUrl: string
}

const MODES = [
  { id: 'balanced', name: 'Balanced', desc: 'Trade off cost, battery life & solar' },
  { id: 'cost_saving', name: 'Cost Saving', desc: 'Prioritize peak price arbitrage' },
  { id: 'battery_life', name: 'Battery Life', desc: 'Minimize throughput & degradation' },
  { id: 'solar_priority', name: 'Solar Priority', desc: 'Maximize clean energy self-consumption' },
  { id: 'backup_priority', name: 'Backup Priority', desc: 'Reserve storage capacity for resilience' },
]

export default function RollingHorizonMPC({ apiUrl }: RollingHorizonMPCProps) {
  const [selectedMode, setSelectedMode] = useState('balanced')
  const [initialSOC, setInitialSOC] = useState(50)
  const [duration, setDuration] = useState(24)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [summary, setSummary] = useState<RollingOptimizationResponse | null>(null)
  const [hourlyData, setHourlyData] = useState<RollingRow[]>([])
  const [comparison, setComparison] = useState<ComparisonRow[]>([])

  // Load benchmark comparison data if available
  useEffect(() => {
    const fetchComparison = async () => {
      try {
        const res = await fetch(`${apiUrl}/results/comparison`)
        if (res.ok) {
          const csvText = await res.text()
          const lines = csvText.trim().split(/\r?\n/)
          if (lines.length > 1) {
            const headers = lines[0].split(',')
            const rows: ComparisonRow[] = lines.slice(1).map((line) => {
              const vals = line.split(',')
              const item: Record<string, string> = {}
              headers.forEach((h, i) => {
                item[h.trim()] = vals[i]?.trim() ?? ''
              })
              return {
                strategy: item.strategy || '',
                display_name: item.display_name || item.strategy || '',
                strategy_type: item.strategy_type || '',
                grid_cost_inr: Number(item.grid_cost_inr || 0),
                battery_throughput_kwh: Number(item.battery_throughput_kwh || 0),
                degradation_cost_inr: Number(item.degradation_cost_inr || 0),
                final_soc_percent: Number(item.final_soc_percent || 0),
                runtime_seconds: Number(item.runtime_seconds || 0),
              }
            })
            setComparison(rows)
          }
        }
      } catch {
        // Comparison not loaded yet; ignore
      }
    }
    fetchComparison()
  }, [apiUrl])

  // Run Rolling-Horizon MPC Simulation
  const runMPC = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await fetch(`${apiUrl}/rolling-optimize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mode: selectedMode,
          initial_soc: initialSOC / 100,
          simulation_duration: duration,
          optimization_horizon: 24,
        }),
      })

      if (!response.ok) {
        const errJson = await response.json()
        throw new Error(errJson.detail || 'Rolling-Horizon MPC request failed.')
      }

      const resData: RollingOptimizationResponse = await response.json()
      setSummary(resData)

      // Fetch the hourly CSV results
      const csvResponse = await fetch(`${apiUrl}/results/rolling/${selectedMode}`)
      if (csvResponse.ok) {
        const csvText = await csvResponse.text()
        const lines = csvText.trim().split(/\r?\n/)
        const headers = lines[0].split(',')

        const rows: RollingRow[] = lines.slice(1).map((line) => {
          const vals = line.split(',')
          const obj: Record<string, string> = {}
          headers.forEach((h, i) => {
            obj[h.trim()] = vals[i]?.trim() ?? ''
          })
          return {
            step: Number(obj.step),
            timestamp: obj.timestamp,
            predicted_demand_kw: Number(obj.predicted_demand_kw),
            actual_demand_kw: Number(obj.actual_demand_kw),
            solar_generation_kw: Number(obj.solar_generation_kw),
            tariff_inr_per_kwh: Number(obj.tariff_inr_per_kwh),
            grid_import_kw: Number(obj.grid_import_kw),
            battery_charge_kw: Number(obj.battery_charge_kw),
            battery_discharge_kw: Number(obj.battery_discharge_kw),
            battery_energy_kwh: Number(obj.battery_energy_kwh),
            battery_soc: Number(obj.battery_soc),
            solar_used_kw: Number(obj.solar_used_kw),
            solar_curtailment_kw: Number(obj.solar_curtailment_kw),
            grid_cost_inr: Number(obj.grid_cost_inr),
            battery_throughput_kwh: Number(obj.battery_throughput_kwh),
            degradation_cost_inr: Number(obj.degradation_cost_inr),
            soc_before: Number(obj.soc_before),
            soc_after: Number(obj.soc_after),
          }
        })
        setHourlyData(rows)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown MPC error')
    } finally {
      setLoading(false)
    }
  }

  const timestamps = hourlyData.map((r) => r.timestamp.slice(11, 16) || `H${r.step}`)

  return (
    <div id="mpc-section" className="space-y-8">
      {/* Header */}
      <div className="flex flex-col justify-between gap-4 border-b border-slate-800 pb-5 md:flex-row md:items-center">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-bold text-white">
              Phase 8: Rolling-Horizon MPC Controller
            </h2>
            <span className="rounded-full bg-cyan-500/10 px-3 py-1 text-xs font-semibold text-cyan-400">
              Model Predictive Control
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-400">
            Dynamic 24-hour receding horizon optimization with closed-loop physical battery state feedback.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Controller Status:</span>
          <span
            className={`rounded-full px-3 py-1 text-xs font-semibold ${
              loading
                ? 'bg-yellow-500/20 text-yellow-400'
                : summary
                  ? 'bg-green-500/20 text-green-400'
                  : 'bg-slate-800 text-slate-400'
            }`}
          >
            ● {loading ? 'Optimizing Iterations...' : summary ? 'Simulation Completed' : 'Ready'}
          </span>
        </div>
      </div>

      {/* Control Panel */}
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <h3 className="mb-4 text-lg font-semibold text-white">
          MPC Simulation Configuration
        </h3>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          {/* Mode Selector */}
          <div>
            <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-slate-400">
              Operating Mode
            </label>
            <select
              value={selectedMode}
              onChange={(e) => setSelectedMode(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-4 py-2.5 text-sm font-medium text-slate-100 focus:border-cyan-400 focus:outline-none"
            >
              {MODES.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name} — {m.desc}
                </option>
              ))}
            </select>
          </div>

          {/* Initial SOC */}
          <div>
            <div className="mb-2 flex justify-between text-xs font-semibold uppercase tracking-wider text-slate-400">
              <span>Initial Battery SOC</span>
              <span className="text-cyan-400">{initialSOC}%</span>
            </div>
            <input
              type="range"
              min={20}
              max={90}
              step={5}
              value={initialSOC}
              onChange={(e) => setInitialSOC(Number(e.target.value))}
              className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-slate-700 accent-cyan-400"
            />
            <div className="mt-1 flex justify-between text-xs text-slate-500">
              <span>20% (Min)</span>
              <span>50%</span>
              <span>90% (Max)</span>
            </div>
          </div>

          {/* Duration */}
          <div>
            <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-slate-400">
              Simulation Duration (Hours)
            </label>
            <select
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-4 py-2.5 text-sm font-medium text-slate-100 focus:border-cyan-400 focus:outline-none"
            >
              <option value={12}>12 Hours (Quick Run)</option>
              <option value={24}>24 Hours (Full Diurnal Day)</option>
              <option value={48}>48 Hours (2 Days Rolling)</option>
              <option value={72}>72 Hours (3 Days Rolling)</option>
            </select>
          </div>
        </div>

        {/* Action Button */}
        <div className="mt-6 flex flex-col items-start gap-4 sm:flex-row sm:items-center">
          <button
            onClick={runMPC}
            disabled={loading}
            className="flex items-center gap-2 rounded-lg bg-cyan-500 px-6 py-3 font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? (
              <>
                <svg className="h-5 w-5 animate-spin text-slate-950" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                <span>Solving Rolling Horizon Steps...</span>
              </>
            ) : (
              <span>Execute Rolling-Horizon MPC</span>
            )}
          </button>

          {error && <span className="text-sm text-red-400">{error}</span>}
        </div>
      </div>

      {/* KPI Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5">
          <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
            <p className="text-xs uppercase text-slate-400">Realized Grid Cost</p>
            <h3 className="mt-2 text-2xl font-bold text-green-400">
              ₹{summary.total_grid_cost.toFixed(2)}
            </h3>
            <p className="mt-1 text-xs text-slate-500">Realized tariff expenditure</p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
            <p className="text-xs uppercase text-slate-400">Battery Throughput</p>
            <h3 className="mt-2 text-2xl font-bold text-cyan-400">
              {summary.total_battery_throughput.toFixed(2)} kWh
            </h3>
            <p className="mt-1 text-xs text-slate-500">Cumulative energy cycled</p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
            <p className="text-xs uppercase text-slate-400">Final Battery SOC</p>
            <h3 className="mt-2 text-2xl font-bold text-purple-400">
              {summary.final_soc_percent.toFixed(1)}%
            </h3>
            <p className="mt-1 text-xs text-slate-500">State of charge at termination</p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
            <p className="text-xs uppercase text-slate-400">Degradation Cost</p>
            <h3 className="mt-2 text-2xl font-bold text-yellow-400">
              ₹{summary.estimated_degradation_cost.toFixed(2)}
            </h3>
            <p className="mt-1 text-xs text-slate-500">Throughput proxy cost</p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
            <p className="text-xs uppercase text-slate-400">Executed Iterations</p>
            <h3 className="mt-2 text-2xl font-bold text-blue-400">
              {summary.iterations_completed} / {duration}
            </h3>
            <p className="mt-1 text-xs text-slate-500">Receding horizon steps solved</p>
          </div>
        </div>
      )}

      {/* Benchmark Comparison Table */}
      {comparison.length > 0 && (
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">
              Benchmark: Rolling-Horizon MPC vs. Static APEMA & Baselines
            </h3>
            <span className="text-xs text-slate-400">24-Hour Evaluation Window</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="border-b border-slate-800 bg-slate-800/50 text-xs uppercase text-slate-400">
                <tr>
                  <th className="px-4 py-3">Strategy</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Grid Cost (₹)</th>
                  <th className="px-4 py-3">Throughput (kWh)</th>
                  <th className="px-4 py-3">Degradation (₹)</th>
                  <th className="px-4 py-3">Final SOC (%)</th>
                  <th className="px-4 py-3">Runtime (s)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {comparison.map((c) => (
                  <tr
                    key={c.strategy}
                    className={`transition hover:bg-slate-800/40 ${
                      c.strategy.includes(selectedMode) ? 'bg-cyan-500/10 font-medium text-cyan-300' : ''
                    }`}
                  >
                    <td className="px-4 py-3 font-semibold">{c.display_name}</td>
                    <td className="px-4 py-3 text-xs capitalize text-slate-400">
                      {c.strategy_type.replace(/_/g, ' ')}
                    </td>
                    <td className="px-4 py-3 font-semibold text-green-400">
                      ₹{c.grid_cost_inr.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-cyan-400">
                      {c.battery_throughput_kwh.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-yellow-400">
                      ₹{c.degradation_cost_inr.toFixed(2)}
                    </td>
                    <td className="px-4 py-3">{c.final_soc_percent.toFixed(1)}%</td>
                    <td className="px-4 py-3 text-slate-400">{c.runtime_seconds.toFixed(2)}s</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Visual Charts */}
      {hourlyData.length > 0 && (
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          {/* 1. Demand: Realized vs Forecast */}
          <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
            <h4 className="mb-4 text-base font-semibold text-white">
              Realized Demand vs. Rolling Forecast (kW)
            </h4>
            <Plot
              data={[
                {
                  x: timestamps,
                  y: hourlyData.map((r) => r.actual_demand_kw),
                  type: 'scatter',
                  mode: 'lines+markers',
                  name: 'Realized Demand',
                  line: { color: '#f43f5e', width: 2.5 },
                },
                {
                  x: timestamps,
                  y: hourlyData.map((r) => r.predicted_demand_kw),
                  type: 'scatter',
                  mode: 'lines',
                  name: '1-Step Forecast',
                  line: { color: '#38bdf8', dash: 'dot', width: 2 },
                },
              ]}
              layout={{
                autosize: true,
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#cbd5e1' },
                xaxis: { title: { text: 'Time' }, gridcolor: '#334155' },
                yaxis: { title: { text: 'Power (kW)' }, gridcolor: '#334155' },
                margin: { l: 60, r: 20, t: 20, b: 60 },
                legend: { orientation: 'h', y: 1.15 },
              }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%', height: '320px' }}
            />
          </div>

          {/* 2. Battery SOC Trajectory */}
          <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
            <h4 className="mb-4 text-base font-semibold text-white">
              Battery State of Charge Trajectory (%)
            </h4>
            <Plot
              data={[
                {
                  x: timestamps,
                  y: hourlyData.map((r) => r.battery_soc * 100),
                  type: 'scatter',
                  mode: 'lines+markers',
                  name: 'Battery SOC',
                  line: { color: '#a78bfa', width: 3 },
                },
              ]}
              layout={{
                autosize: true,
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#cbd5e1' },
                xaxis: { title: { text: 'Time' }, gridcolor: '#334155' },
                yaxis: { title: { text: 'SOC (%)' }, range: [0, 100], gridcolor: '#334155' },
                shapes: [
                  {
                    type: 'line',
                    y0: 20,
                    y1: 20,
                    x0: timestamps[0],
                    x1: timestamps[timestamps.length - 1],
                    line: { color: '#ef4444', width: 1.5, dash: 'dash' },
                  },
                  {
                    type: 'line',
                    y0: 90,
                    y1: 90,
                    x0: timestamps[0],
                    x1: timestamps[timestamps.length - 1],
                    line: { color: '#10b981', width: 1.5, dash: 'dash' },
                  },
                ],
                margin: { l: 60, r: 20, t: 20, b: 60 },
              }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%', height: '320px' }}
            />
          </div>

          {/* 3. Diverging Battery Charging / Discharging */}
          <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
            <h4 className="mb-4 text-base font-semibold text-white">
              Battery Charging & Discharging Decisions (kW)
            </h4>
            <Plot
              data={[
                {
                  x: timestamps,
                  y: hourlyData.map((r) => r.battery_charge_kw),
                  type: 'bar',
                  name: 'Charging (+kW)',
                  marker: { color: '#22c55e' },
                },
                {
                  x: timestamps,
                  y: hourlyData.map((r) => -r.battery_discharge_kw),
                  type: 'bar',
                  name: 'Discharging (-kW)',
                  marker: { color: '#f97316' },
                },
              ]}
              layout={{
                autosize: true,
                barmode: 'relative',
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#cbd5e1' },
                xaxis: { title: { text: 'Time' }, gridcolor: '#334155' },
                yaxis: { title: { text: 'Power (kW)' }, gridcolor: '#334155' },
                margin: { l: 60, r: 20, t: 20, b: 60 },
                legend: { orientation: 'h', y: 1.15 },
              }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%', height: '320px' }}
            />
          </div>

          {/* 4. Realized Grid Import & Tariff Cost */}
          <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
            <h4 className="mb-4 text-base font-semibold text-white">
              Realized Grid Electricity Import (kW)
            </h4>
            <Plot
              data={[
                {
                  x: timestamps,
                  y: hourlyData.map((r) => r.grid_import_kw),
                  type: 'bar',
                  name: 'Grid Import',
                  marker: { color: '#06b6d4' },
                },
              ]}
              layout={{
                autosize: true,
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#cbd5e1' },
                xaxis: { title: { text: 'Time' }, gridcolor: '#334155' },
                yaxis: { title: { text: 'Grid Import (kW)' }, rangemode: 'tozero', gridcolor: '#334155' },
                margin: { l: 60, r: 20, t: 20, b: 60 },
              }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%', height: '320px' }}
            />
          </div>
        </div>
      )}
    </div>
  )
}

