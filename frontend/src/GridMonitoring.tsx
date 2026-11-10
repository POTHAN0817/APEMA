interface GridRow {
  demand_kw: number
  grid_import_kw: number
  grid_cost_inr: number
}

interface GridMonitoringProps {
  data: GridRow[]
}

function GridMonitoring({ data }: GridMonitoringProps) {

  // Total grid electricity imported over the 24-hour period.
  const totalGridImport = data.reduce(
    (sum, row) => sum + row.grid_import_kw,
    0,
  )

  // Peak hourly grid import.
  const peakGridImport = Math.max(
    0,
    ...data.map((row) => row.grid_import_kw),
  )

  // Average hourly grid import.
  const averageGridImport =
    data.length > 0
      ? totalGridImport / data.length
      : 0

  // Total grid electricity cost.
  const totalGridCost = data.reduce(
    (sum, row) => sum + row.grid_cost_inr,
    0,
  )

  // Total building demand.
  const totalDemand = data.reduce(
    (sum, row) => sum + row.demand_kw,
    0,
  )

  // Percentage of demand supplied by the grid.
  const gridDependency =
    totalDemand > 0
      ? (totalGridImport / totalDemand) * 100
      : 0

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">

      {/* Header */}
      <div className="mb-6 flex items-center justify-between">

        <div>
          <h2 className="text-xl font-bold text-white">
            Grid Energy Monitoring
          </h2>

          <p className="mt-1 text-sm text-slate-400">
            Electricity import and grid dependency
          </p>
        </div>

        <span className="rounded-full bg-blue-500/10 px-3 py-2 text-sm text-blue-400">
          ⚡ Grid
        </span>

      </div>

      {/* Main Grid Import */}
      <div className="mb-5 rounded-lg bg-slate-800 p-5">

        <p className="text-sm text-slate-400">
          Total Grid Electricity Imported
        </p>

        <h3 className="mt-2 text-4xl font-bold text-blue-400">
          {totalGridImport.toFixed(2)} kWh
        </h3>

        <p className="mt-2 text-sm text-slate-400">
          Total electricity purchased from the grid
        </p>

      </div>

      {/* Grid Metrics */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">

        <div className="rounded-lg border border-slate-700 p-4">

          <p className="text-sm text-slate-400">
            Peak Grid Import
          </p>

          <p className="mt-2 text-2xl font-bold text-orange-400">
            {peakGridImport.toFixed(2)} kW
          </p>

        </div>

        <div className="rounded-lg border border-slate-700 p-4">

          <p className="text-sm text-slate-400">
            Average Grid Import
          </p>

          <p className="mt-2 text-2xl font-bold text-cyan-400">
            {averageGridImport.toFixed(2)} kW
          </p>

        </div>

        <div className="rounded-lg border border-slate-700 p-4">

          <p className="text-sm text-slate-400">
            Grid Electricity Cost
          </p>

          <p className="mt-2 text-2xl font-bold text-green-400">
            ₹{totalGridCost.toFixed(2)}
          </p>

        </div>

        <div className="rounded-lg border border-slate-700 p-4">

          <p className="text-sm text-slate-400">
            Grid Dependency
          </p>

          <p className="mt-2 text-2xl font-bold text-purple-400">
            {gridDependency.toFixed(2)}%
          </p>

        </div>

      </div>

      {/* Grid Dependency Progress */}
      <div className="mt-6">

        <div className="mb-2 flex justify-between">

          <p className="text-sm text-slate-400">
            Grid Dependency Level
          </p>

          <p className="font-bold text-purple-400">
            {gridDependency.toFixed(1)}%
          </p>

        </div>

        <div className="h-4 overflow-hidden rounded-full bg-slate-700">

          <div
            className="h-full rounded-full bg-purple-500 transition-all duration-700"
            style={{
              width: `${Math.min(100, Math.max(0, gridDependency))}%`,
            }}
          />

        </div>

      </div>

      <p className="mt-4 text-xs text-slate-500">
        Calculated from hourly optimization results.
        Energy totals assume one-hour intervals.
      </p>

    </div>
  )
}

export default GridMonitoring