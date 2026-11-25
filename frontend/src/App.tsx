import { useEffect, useState } from 'react'
import EnergyCharts from './EnergyCharts'
import BatterySOC from './BatterySOC'
import SolarIndicator from './SolarIndicator'
import GridMonitoring from './GridMonitoring'
import BatteryAnalysis from './BatteryAnalysis'
import ElectricityCostAnalysis from './ElectricityCostAnalysis'
import SolarAnalysis from './SolarAnalysis'
import GridDependencyAnalysis from './GridDependencyAnalysis'
import EnergyScheduling from './EnergyScheduling'
import RollingHorizonMPC from './RollingHorizonMPC'

interface OptimizationResult {
  mode: string
  objective_value: number
  total_grid_cost_inr: number
  battery_throughput_kwh: number
  final_soc_percent: number
  results_file: string
}

interface EnergyRow {
  timestamp: string
  demand_kw: number
  solar_kw: number
  tariff_inr_per_kwh: number
  grid_import_kw: number
  battery_charge_kw: number
  battery_discharge_kw: number
  battery_soc: number
  solar_used_kw: number
  solar_curtailment_kw: number
  grid_cost_inr: number
}

const API_URL = 'http://127.0.0.1:8000'

const modes = [
  {
    id: 'cost_saving',
    name: 'Cost Saving',
    description: 'Reduce electricity costs using price-aware scheduling.',
  },
  {
    id: 'battery_life',
    name: 'Battery Life',
    description: 'Reduce battery cycling and degradation.',
  },
  {
    id: 'solar_priority',
    name: 'Solar Priority',
    description: 'Prioritize solar energy utilization.',
  },
  {
    id: 'backup_priority',
    name: 'Backup Priority',
    description: 'Maintain additional battery energy for backup.',
  },
  {
    id: 'balanced',
    name: 'Balanced',
    description: 'Balance electricity cost, solar usage and battery life.',
  },
]

function App() {
  const [selectedMode, setSelectedMode] = useState('balanced')
  const [result, setResult] = useState<OptimizationResult | null>(null)
  const [hourlyData, setHourlyData] = useState<EnergyRow[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [apiStatus, setApiStatus] = useState('Checking')

  // Check whether the FastAPI backend is running.
  const checkAPI = async () => {
    try {
      const response = await fetch(`${API_URL}/`)

      if (!response.ok) {
        throw new Error('Backend unavailable')
      }

      setApiStatus('Connected')
    } catch {
      setApiStatus('Disconnected')
    }
  }

  // Check API when the dashboard first loads.
  useEffect(() => {
    checkAPI()
  }, [])

  // Run optimization for the selected mode.
  const runOptimization = async () => {
    setLoading(true)
    setError('')
    setResult(null)
    setHourlyData([])

    try {
      const response = await fetch(
        `${API_URL}/optimize/${selectedMode}`,
      )

      if (!response.ok) {
        throw new Error('Optimization request failed.')
      }

      const data: OptimizationResult = await response.json()
      setResult(data)

      // Download the hourly optimization results.
      const csvResponse = await fetch(
        `${API_URL}/results/${selectedMode}`,
      )

      if (!csvResponse.ok) {
        throw new Error('Unable to retrieve optimization results.')
      }

      const csvText = await csvResponse.text()

      // Convert CSV data into chart-friendly rows.
      const lines = csvText.trim().split(/\r?\n/)
      const headers = lines[0].split(',')

      const rows: EnergyRow[] = lines.slice(1).map((line) => {
        const values = line.split(',')

        const row: Record<string, string> = {}

        headers.forEach((header, index) => {
          row[header.trim()] = values[index]?.trim() ?? ''
        })

        return {
          timestamp: row.timestamp,
          demand_kw: Number(row.demand_kw),
          solar_kw: Number(row.solar_kw),
          tariff_inr_per_kwh: Number(row.tariff_inr_per_kwh),
          grid_import_kw: Number(row.grid_import_kw),
          battery_charge_kw: Number(row.battery_charge_kw),
          battery_discharge_kw: Number(row.battery_discharge_kw),
          battery_soc: Number(row.battery_soc),
          solar_used_kw: Number(row.solar_used_kw),
          solar_curtailment_kw: Number(row.solar_curtailment_kw),
          grid_cost_inr: Number(row.grid_cost_inr),
        }
      })

      setHourlyData(rows)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Something went wrong.',
      )
    } finally {
      setLoading(false)
      checkAPI()
    }
  }

  const selectedModeDetails = modes.find(
    (mode) => mode.id === selectedMode,
  )

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">

      {/* Sidebar */}
      <aside className="fixed left-0 top-0 hidden h-screen w-64 border-r border-slate-800 bg-slate-900 p-6 lg:block">

        <div className="mb-10">
          <h1 className="text-3xl font-bold text-cyan-400">
            APEMA
          </h1>

          <p className="mt-2 text-sm text-slate-400">
            Energy Management System
          </p>
        </div>

        <nav className="space-y-4">
          <a
            href="#dashboard"
            className="block rounded-lg bg-cyan-500/10 px-4 py-3 text-cyan-400"
          >
            Dashboard
          </a>

          <a
            href="#modes"
            className="block rounded-lg px-4 py-3 text-slate-300 hover:bg-slate-800"
          >
            Energy Modes
          </a>

          <a
            href="#charts"
            className="block rounded-lg px-4 py-3 text-slate-300 hover:bg-slate-800"
          >
            Energy Charts
          </a>

          <a
            href="#mpc-section"
            className="block rounded-lg px-4 py-3 text-cyan-400 hover:bg-slate-800"
          >
            Rolling-Horizon MPC
          </a>

          <a
            href="#architecture"
            className="block rounded-lg px-4 py-3 text-slate-300 hover:bg-slate-800"
          >
            Architecture
          </a>
        </nav>

        <div className="absolute bottom-6 left-6 right-6 rounded-lg bg-slate-800 p-4">
          <p className="text-xs text-slate-400">
            Backend Status
          </p>

          <p
            className={`mt-2 font-semibold ${
              apiStatus === 'Connected'
                ? 'text-green-400'
                : apiStatus === 'Disconnected'
                  ? 'text-red-400'
                  : 'text-yellow-400'
            }`}
          >
            ● {apiStatus}
          </p>
        </div>
      </aside>

      {/* Main Dashboard */}
      <main
        id="dashboard"
        className="p-5 lg:ml-64 lg:p-10"
      >

        {/* Header */}
        <header className="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-center">

          <div>
            <h2 className="text-3xl font-bold">
              Energy Management Dashboard
            </h2>

            <p className="mt-2 text-slate-400">
              Dynamic Price-Aware Solar, Battery & Grid Energy Management
            </p>
          </div>

          <div className="rounded-lg border border-slate-700 bg-slate-900 px-4 py-3">
            <span className="text-sm text-slate-400">
              System Status
            </span>

            <p className="font-semibold text-green-400">
              ● {apiStatus}
            </p>
          </div>
        </header>

        {/* Summary Cards */}
        <section className="mb-8 grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-4">

          <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
            <p className="text-sm text-slate-400">
              Solar Capacity
            </p>

            <h3 className="mt-3 text-3xl font-bold text-yellow-400">
              100 kW
            </h3>

            <p className="mt-2 text-xs text-slate-500">
              Configured PV capacity
            </p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
            <p className="text-sm text-slate-400">
              Battery Capacity
            </p>

            <h3 className="mt-3 text-3xl font-bold text-cyan-400">
              200 kWh
            </h3>

            <p className="mt-2 text-xs text-slate-500">
              Configured storage capacity
            </p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
            <p className="text-sm text-slate-400">
              Maximum Battery Power
            </p>

            <h3 className="mt-3 text-3xl font-bold text-purple-400">
              50 kW
            </h3>

            <p className="mt-2 text-xs text-slate-500">
              Charge and discharge limit
            </p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
            <p className="text-sm text-slate-400">
              Operating Modes
            </p>

            <h3 className="mt-3 text-3xl font-bold text-green-400">
              5
            </h3>

            <p className="mt-2 text-xs text-slate-500">
              APEMA management strategies
            </p>
          </div>

        </section>

        {/* Operating Modes */}
        <section id="modes" className="mb-8">

          <div className="mb-5">
            <h2 className="text-2xl font-bold">
              Energy Management Modes
            </h2>

            <p className="mt-2 text-slate-400">
              Select an operating strategy for the optimization algorithm.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">

            {modes.map((mode) => (
              <button
                key={mode.id}
                onClick={() => setSelectedMode(mode.id)}
                className={`rounded-xl border p-5 text-left transition ${
                  selectedMode === mode.id
                    ? 'border-cyan-400 bg-cyan-500/10'
                    : 'border-slate-800 bg-slate-900 hover:border-slate-600'
                }`}
              >
                <div className="flex items-center justify-between">

                  <h3 className="text-lg font-semibold">
                    {mode.name}
                  </h3>

                  <span
                    className={`h-3 w-3 rounded-full ${
                      selectedMode === mode.id
                        ? 'bg-cyan-400'
                        : 'bg-slate-600'
                    }`}
                  />
                </div>

                <p className="mt-3 text-sm text-slate-400">
                  {mode.description}
                </p>

              </button>
            ))}

          </div>
        </section>

        {/* Run Optimization */}
        <section className="mb-8 rounded-xl border border-slate-800 bg-slate-900 p-6">

          <h2 className="text-xl font-bold">
            Run APEMA Optimization
          </h2>

          <p className="mt-2 text-slate-400">
            Selected strategy:
            {' '}
            <span className="font-semibold text-cyan-400">
              {selectedModeDetails?.name}
            </span>
          </p>

          <button
            onClick={runOptimization}
            disabled={loading || apiStatus === 'Disconnected'}
            className="mt-5 rounded-lg bg-cyan-500 px-6 py-3 font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? 'Optimizing...' : 'Run Optimization'}
          </button>

          {error && (
            <p className="mt-4 text-red-400">
              {error}
            </p>
          )}

        </section>

        {/* Optimization Results */}
        {result && (
          <section className="mb-8">

            <h2 className="mb-5 text-2xl font-bold">
              Optimization Results
            </h2>

            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-4">

              <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
                <p className="text-sm text-slate-400">
                  Grid Electricity Cost
                </p>

                <h3 className="mt-3 text-2xl font-bold text-green-400">
                  ₹{result.total_grid_cost_inr.toFixed(2)}
                </h3>
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
                <p className="text-sm text-slate-400">
                  Battery Throughput
                </p>

                <h3 className="mt-3 text-2xl font-bold text-cyan-400">
                  {result.battery_throughput_kwh.toFixed(2)} kWh
                </h3>
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
                <p className="text-sm text-slate-400">
                  Final Battery SOC
                </p>

                <h3 className="mt-3 text-2xl font-bold text-purple-400">
                  {result.final_soc_percent.toFixed(1)}%
                </h3>
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
                <p className="text-sm text-slate-400">
                  Optimization Objective
                </p>

                <h3 className="mt-3 text-2xl font-bold text-yellow-400">
                  ₹{result.objective_value.toFixed(2)}
                </h3>
              </div>

            </div>
          </section>
        )}
        {/* Battery State of Charge */}
        {result && (
          <section className="mb-8">
            <BatterySOC
              soc={result.final_soc_percent}
              capacity={200}
            />
          </section>
        )}
        {/* Solar Energy Indicator */}
        {hourlyData.length > 0 && (
          <section className="mb-8">
            <SolarIndicator data={hourlyData} />
          </section>
        )}
        {/* Grid Energy Monitoring */}
        {hourlyData.length > 0 && (
          <section className="mb-8">
            <GridMonitoring data={hourlyData} />
          </section>
        )}
        {/* Battery Charge and Discharge Analysis */}
        {hourlyData.length > 0 && (
          <section className="mb-8">
            <BatteryAnalysis
              data={hourlyData}
              capacityKwh={200}
            />
          </section>
        )}
        {/* Electricity Cost Analysis */}
        {hourlyData.length > 0 && (
          <section className="mb-8">
            <ElectricityCostAnalysis data={hourlyData} />
          </section>
        )}
        {/* Solar Energy Utilization Analysis */}
        {hourlyData.length > 0 && (
          <section className="mb-8">
            <SolarAnalysis data={hourlyData} />
          </section>
        )}
        {/* Grid Dependency and Energy Independence Analysis */}
        {hourlyData.length > 0 && (
          <section className="mb-8">
            <GridDependencyAnalysis data={hourlyData} />
          </section>
        )}
        {/* Energy Scheduling Analysis */}
        {hourlyData.length > 0 && (
          <section className="mb-8">
            <EnergyScheduling data={hourlyData} />
          </section>
        )}
        {/* Energy Charts */}
        {hourlyData.length > 0 && (
          <section id="charts" className="mb-8">

            <h2 className="mb-2 text-2xl font-bold">
              Hourly Energy Performance
            </h2>

            <p className="mb-5 text-sm text-slate-400">
              Hourly simulation results for the selected operating mode.
            </p>

            <EnergyCharts data={hourlyData} />

          </section>
        )}

        {/* Rolling-Horizon Model Predictive Control Section */}
        <section className="mb-10">
          <RollingHorizonMPC apiUrl={API_URL} />
        </section>

        {/* Architecture */}
        <section
          id="architecture"
          className="mb-8 rounded-xl border border-slate-800 bg-slate-900 p-6"
        >

          <h2 className="mb-5 text-2xl font-bold">
            APEMA System Architecture
          </h2>

          <div className="grid grid-cols-1 gap-3 text-center sm:grid-cols-2 lg:grid-cols-4">

            {[
              'Input Data',
              'Demand & Solar Forecasting',
              'Battery Model',
              'APEMA Optimization',
              'Energy Decision',
              'Performance Evaluation',
              'Hourly Update',
            ].map((item, index) => (
              <div
                key={item}
                className="rounded-lg border border-slate-700 bg-slate-800 p-4"
              >
                <span className="text-xs text-cyan-400">
                  STEP {index + 1}
                </span>

                <p className="mt-2 font-semibold">
                  {item}
                </p>
              </div>
            ))}

          </div>
        </section>

        {/* Footer */}
        <footer className="border-t border-slate-800 py-6 text-center text-sm text-slate-500">

          <p>
            APEMA — Adaptive Price-Aware Energy Management Algorithm
          </p>

          <p className="mt-2">
            Python · FastAPI · React · TypeScript · Plotly.js
          </p>

        </footer>

      </main>
    </div>
  )
}

export default App