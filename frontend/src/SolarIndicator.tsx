interface SolarRow {
  solar_kw: number
  solar_used_kw: number
  solar_curtailment_kw: number
}

interface SolarIndicatorProps {
  data: SolarRow[]
}

function SolarIndicator({ data }: SolarIndicatorProps) {
  const totalGenerated = data.reduce(
    (sum, row) => sum + row.solar_kw,
    0,
  )

  const totalUsed = data.reduce(
    (sum, row) => sum + row.solar_used_kw,
    0,
  )

  const totalCurtailed = data.reduce(
    (sum, row) => sum + row.solar_curtailment_kw,
    0,
  )

  const utilization =
    totalGenerated > 0
      ? (totalUsed / totalGenerated) * 100
      : 0

  const peakGeneration = Math.max(
    0,
    ...data.map((row) => row.solar_kw),
  )

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">

      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">
            Solar Energy Status
          </h2>

          <p className="mt-1 text-sm text-slate-400">
            Solar PV generation and utilization
          </p>
        </div>

        <span className="rounded-full bg-yellow-500/10 px-3 py-2 text-sm text-yellow-400">
          ☀ Solar PV
        </span>
      </div>

      {/* Main Solar Generation */}
      <div className="mb-6 rounded-lg bg-slate-800 p-5">

        <p className="text-sm text-slate-400">
          Total Solar Energy Generated
        </p>

        <h3 className="mt-2 text-4xl font-bold text-yellow-400">
          {totalGenerated.toFixed(2)} kWh
        </h3>

        <p className="mt-2 text-sm text-slate-400">
          Peak Generation: {peakGeneration.toFixed(2)} kW
        </p>

      </div>

      {/* Solar Metrics */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">

        <div className="rounded-lg border border-slate-700 p-4">
          <p className="text-sm text-slate-400">
            Solar Energy Used
          </p>

          <p className="mt-2 text-2xl font-bold text-green-400">
            {totalUsed.toFixed(2)} kWh
          </p>
        </div>

        <div className="rounded-lg border border-slate-700 p-4">
          <p className="text-sm text-slate-400">
            Solar Energy Curtailed
          </p>

          <p className="mt-2 text-2xl font-bold text-orange-400">
            {totalCurtailed.toFixed(2)} kWh
          </p>
        </div>

      </div>

      {/* Utilization */}
      <div className="mt-6">

        <div className="mb-2 flex justify-between">
          <p className="text-sm text-slate-400">
            Solar Utilization
          </p>

          <p className="font-bold text-yellow-400">
            {utilization.toFixed(1)}%
          </p>
        </div>

        <div className="h-4 overflow-hidden rounded-full bg-slate-700">

          <div
            className="h-full rounded-full bg-yellow-400 transition-all duration-700"
            style={{
              width: `${Math.min(100, Math.max(0, utilization))}%`,
            }}
          />

        </div>

      </div>

      <p className="mt-4 text-xs text-slate-500">
        Calculated from the hourly optimization results.
        Energy totals assume one-hour intervals.
      </p>

    </div>
  )
}

export default SolarIndicator