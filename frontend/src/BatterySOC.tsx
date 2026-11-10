interface BatterySOCProps {
  soc: number
  capacity: number
}

function BatterySOC({ soc, capacity }: BatterySOCProps) {
  const safeSOC = Math.max(0, Math.min(100, soc))
  const storedEnergy = (safeSOC / 100) * capacity

  const getBatteryColor = () => {
    if (safeSOC <= 25) return 'bg-red-500'
    if (safeSOC <= 50) return 'bg-yellow-400'
    return 'bg-green-400'
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">

      <div className="mb-5 flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">
          Battery Status
        </h2>

        <span className="rounded-full bg-cyan-500/10 px-3 py-1 text-sm text-cyan-400">
          Energy Storage
        </span>
      </div>

      <div className="flex items-center gap-6">

        {/* Battery illustration */}
        <div className="relative h-28 w-20 rounded-lg border-4 border-slate-400 p-1">
          <div className="absolute -top-3 left-6 h-2 w-10 rounded-t bg-slate-400" />

          <div className="flex h-full flex-col justify-end overflow-hidden rounded-sm bg-slate-800">
            <div
              className={`w-full transition-all duration-700 ${getBatteryColor()}`}
              style={{ height: `${safeSOC}%` }}
            />
          </div>
        </div>

        {/* Battery information */}
        <div className="flex-1">

          <p className="text-4xl font-bold text-cyan-400">
            {safeSOC.toFixed(1)}%
          </p>

          <p className="mt-2 text-sm text-slate-400">
            State of Charge
          </p>

          <p className="mt-4 text-lg font-semibold text-white">
            {storedEnergy.toFixed(2)} kWh
          </p>

          <p className="text-sm text-slate-400">
            Stored Energy / {capacity} kWh
          </p>

        </div>
      </div>

      {/* SOC progress bar */}
      <div className="mt-6">

        <div className="mb-2 flex justify-between text-xs text-slate-400">
          <span>0%</span>
          <span>Battery Capacity</span>
          <span>100%</span>
        </div>

        <div className="h-3 overflow-hidden rounded-full bg-slate-700">
          <div
            className={`h-full rounded-full transition-all duration-700 ${getBatteryColor()}`}
            style={{ width: `${safeSOC}%` }}
          />
        </div>

      </div>

      {/* Battery limits */}
      <div className="mt-5 grid grid-cols-2 gap-3">

        <div className="rounded-lg bg-slate-800 p-3">
          <p className="text-xs text-slate-400">
            Minimum SOC
          </p>

          <p className="mt-1 font-semibold text-red-400">
            20%
          </p>
        </div>

        <div className="rounded-lg bg-slate-800 p-3">
          <p className="text-xs text-slate-400">
            Maximum SOC
          </p>

          <p className="mt-1 font-semibold text-green-400">
            90%
          </p>
        </div>

      </div>

    </div>
  )
}

export default BatterySOC