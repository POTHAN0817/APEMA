import Plot from 'react-plotly.js'

interface GridDependencyRow {
  timestamp: string
  demand_kw: number
  grid_import_kw: number
  solar_used_kw: number
  battery_discharge_kw: number
}

interface GridDependencyAnalysisProps {
  data: GridDependencyRow[]
}

function GridDependencyAnalysis({
  data,
}: GridDependencyAnalysisProps) {

  const TIME_STEP_HOURS = 1

  if (data.length === 0) {
    return (
      <div className="rounded-xl border border-slate-700 bg-slate-900 p-6 text-slate-300">
        Run an optimization to view grid dependency analysis.
      </div>
    )
  }

  const totalDemand = data.reduce(
    (sum, row) => sum + row.demand_kw * TIME_STEP_HOURS,
    0
  )

  const totalGridImport = data.reduce(
    (sum, row) => sum + row.grid_import_kw * TIME_STEP_HOURS,
    0
  )

  const totalSolarContribution = data.reduce(
    (sum, row) => sum + row.solar_used_kw * TIME_STEP_HOURS,
    0
  )

  const totalBatteryContribution = data.reduce(
    (sum, row) => sum + row.battery_discharge_kw * TIME_STEP_HOURS,
    0
  )

  const percentage = (value: number) =>
    totalDemand > 0 ? (value / totalDemand) * 100 : 0

  const gridDependency = percentage(totalGridImport)

  const solarContribution = percentage(totalSolarContribution)

  const batteryContribution = percentage(totalBatteryContribution)

  const energyIndependence =
    percentage(totalSolarContribution + totalBatteryContribution)

  return (
    <div className="space-y-6">

      {/* Heading */}
      <div>
        <h2 className="text-xl font-semibold text-white">
          Grid Dependency & Energy Independence
        </h2>

        <p className="mt-1 text-sm text-slate-400">
          Evaluation of building energy supply from grid, solar and battery.
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">

        <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">
            Total Grid Import
          </p>

          <h3 className="mt-2 text-2xl font-bold text-cyan-400">
            {totalGridImport.toFixed(2)} kWh
          </h3>
        </div>

        <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">
            Grid Dependency
          </p>

          <h3 className="mt-2 text-2xl font-bold text-orange-400">
            {gridDependency.toFixed(2)}%
          </h3>
        </div>

        <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">
            Solar Contribution
          </p>

          <h3 className="mt-2 text-2xl font-bold text-yellow-400">
            {solarContribution.toFixed(2)}%
          </h3>
        </div>

        <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">
            Battery Contribution
          </p>

          <h3 className="mt-2 text-2xl font-bold text-purple-400">
            {batteryContribution.toFixed(2)}%
          </h3>
        </div>

      </div>

      {/* Energy Independence */}
      <div className="rounded-xl border border-green-500/30 bg-slate-900 p-6">

        <h3 className="text-lg font-semibold text-white">
          Energy Independence
        </h3>

        <h2 className="mt-3 text-4xl font-bold text-green-400">
          {energyIndependence.toFixed(2)}%
        </h2>

        <div className="mt-4 h-4 overflow-hidden rounded-full bg-slate-700">

          <div
            className="h-full rounded-full bg-green-500 transition-all"
            style={{
              width: `${Math.min(100, Math.max(0, energyIndependence))}%`,
            }}
          />

        </div>

        <p className="mt-3 text-sm text-slate-400">
          Percentage of building demand supplied by solar and battery
          discharge rather than grid electricity.
        </p>

      </div>

      {/* Hourly Grid Import */}
      <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">

        <h3 className="mb-4 text-lg font-semibold text-white">
          Hourly Grid Electricity Import
        </h3>

        <Plot
          data={[
            {
              x: data.map((row) => row.timestamp),
              y: data.map((row) => row.grid_import_kw),
              type: 'bar',
              name: 'Grid Import',
              marker: {
                color: '#06b6d4',
              },
            },
          ]}
          layout={{
            autosize: true,
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: {
              color: '#cbd5e1',
            },
            xaxis: {
              title: { text: 'Time' },
              gridcolor: '#334155',
            },
            yaxis: {
              title: { text: 'Grid Import (kW)' },
              gridcolor: '#334155',
              rangemode: 'tozero',
            },
            margin: {
              l: 70,
              r: 20,
              t: 30,
              b: 70,
            },
          }}
          config={{ responsive: true }}
          style={{
            width: '100%',
            height: '350px',
          }}
        />

      </div>

      {/* Energy Source Distribution */}
      <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">

        <h3 className="mb-4 text-lg font-semibold text-white">
          Building Energy Source Distribution
        </h3>

        <Plot
          data={[
            {
              labels: [
                'Grid Electricity',
                'Solar Energy',
                'Battery Discharge',
              ],
              values: [
                totalGridImport,
                totalSolarContribution,
                totalBatteryContribution,
              ],
              type: 'pie',
              hole: 0.55,
              marker: {
                colors: [
                  '#06b6d4',
                  '#eab308',
                  '#a78bfa',
                ],
              },
              textinfo: 'label+percent',
              hovertemplate:
                '%{label}: %{value:.2f} kWh<extra></extra>',
            },
          ]}
          layout={{
            autosize: true,
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: {
              color: '#cbd5e1',
            },
            showlegend: true,
            margin: {
              l: 20,
              r: 20,
              t: 20,
              b: 20,
            },
          }}
          config={{ responsive: true }}
          style={{
            width: '100%',
            height: '350px',
          }}
        />

      </div>

      {/* Energy Assessment */}
      <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">

        <h3 className="text-lg font-semibold text-white">
          Energy Dependency Assessment
        </h3>

        <div className="mt-4 space-y-3 text-sm">

          <p className="text-slate-400">
            Total Building Demand:{' '}
            <span className="font-semibold text-white">
              {totalDemand.toFixed(2)} kWh
            </span>
          </p>

          <p className="text-slate-400">
            Grid Dependency:{' '}
            <span className="font-semibold text-orange-400">
              {gridDependency.toFixed(2)}%
            </span>
          </p>

          <p className="text-slate-400">
            Energy Independence:{' '}
            <span className="font-semibold text-green-400">
              {energyIndependence.toFixed(2)}%
            </span>
          </p>

        </div>

        <p className="mt-4 text-xs text-slate-500">
          Results are based on the current simulated 24-hour energy schedule.
          Energy independence represents the share of demand supplied by
          solar and battery discharge. It does not represent off-grid
          capability or long-term energy autonomy.
        </p>

      </div>

    </div>
  )
}

export default GridDependencyAnalysis