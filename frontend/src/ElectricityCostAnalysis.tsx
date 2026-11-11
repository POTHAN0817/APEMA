import Plot from 'react-plotly.js'

interface CostRow {
  timestamp: string
  grid_import_kw: number
  tariff_inr_per_kwh: number
  grid_cost_inr: number
}

interface ElectricityCostAnalysisProps {
  data: CostRow[]
}

function ElectricityCostAnalysis({
  data,
}: ElectricityCostAnalysisProps) {

  const TIME_STEP_HOURS = 1

  if (data.length === 0) {
    return (
      <div className="rounded-xl border border-slate-700 bg-slate-900 p-6 text-slate-300">
        Run an optimization to view electricity cost analysis.
      </div>
    )
  }

  const totalCost = data.reduce(
    (sum, row) => sum + row.grid_cost_inr,
    0
  )

  const totalGridEnergy = data.reduce(
    (sum, row) =>
      sum + row.grid_import_kw * TIME_STEP_HOURS,
    0
  )

  const averageHourlyCost = totalCost / data.length

  const highestCostRow = data.reduce(
    (highest, row) =>
      row.grid_cost_inr > highest.grid_cost_inr
        ? row
        : highest,
    data[0]
  )

  const averageTariff =
    totalGridEnergy > 0
      ? totalCost / totalGridEnergy
      : 0

  return (
    <div className="space-y-6">

      {/* Heading */}
      <div>
        <h2 className="text-xl font-semibold text-white">
          Electricity Cost Analysis
        </h2>

        <p className="mt-1 text-sm text-slate-400">
          Analysis of grid electricity consumption and tariff-based operating costs.
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">

        <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">
            Total Electricity Cost
          </p>

          <h3 className="mt-2 text-2xl font-bold text-green-400">
            ₹{totalCost.toFixed(2)}
          </h3>
        </div>

        <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">
            Total Grid Energy
          </p>

          <h3 className="mt-2 text-2xl font-bold text-cyan-400">
            {totalGridEnergy.toFixed(2)} kWh
          </h3>
        </div>

        <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">
            Average Hourly Cost
          </p>

          <h3 className="mt-2 text-2xl font-bold text-yellow-400">
            ₹{averageHourlyCost.toFixed(2)}
          </h3>
        </div>

        <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">
            Average Effective Tariff
          </p>

          <h3 className="mt-2 text-2xl font-bold text-purple-400">
            ₹{averageTariff.toFixed(2)}/kWh
          </h3>
        </div>

      </div>

      {/* Hourly Electricity Cost Chart */}
      <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">

        <h3 className="mb-4 text-lg font-semibold text-white">
          Hourly Electricity Cost
        </h3>

        <Plot
          data={[
            {
              x: data.map((row) => row.timestamp),
              y: data.map((row) => row.grid_cost_inr),
              type: 'bar',
              name: 'Electricity Cost',
              marker: {
                color: '#22d3ee',
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
              title: { text: 'Cost (₹)' },
              gridcolor: '#334155',
              rangemode: 'tozero',
            },
            margin: {
              l: 65,
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

      {/* Grid Energy vs Cost */}
      <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">

        <h3 className="mb-4 text-lg font-semibold text-white">
          Grid Energy Consumption vs Electricity Cost
        </h3>

        <Plot
          data={[
            {
              x: data.map((row) => row.grid_import_kw),
              y: data.map((row) => row.grid_cost_inr),
              type: 'scatter',
              mode: 'markers',
              name: 'Hourly Grid Import',
              marker: {
                color: '#a78bfa',
                size: 10,
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
              title: { text: 'Grid Import (kW)' },
              gridcolor: '#334155',
            },
            yaxis: {
              title: { text: 'Electricity Cost (₹)' },
              gridcolor: '#334155',
            },
            margin: {
              l: 65,
              r: 20,
              t: 30,
              b: 60,
            },
          }}
          config={{ responsive: true }}
          style={{
            width: '100%',
            height: '350px',
          }}
        />

      </div>

      {/* Highest Cost Hour */}
      <div className="rounded-xl border border-orange-500/30 bg-slate-900 p-5">

        <h3 className="text-lg font-semibold text-white">
          Highest Electricity Cost Hour
        </h3>

        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">

          <div>
            <p className="text-sm text-slate-400">
              Timestamp
            </p>

            <p className="mt-1 font-semibold text-white">
              {highestCostRow.timestamp}
            </p>
          </div>

          <div>
            <p className="text-sm text-slate-400">
              Grid Import
            </p>

            <p className="mt-1 font-semibold text-cyan-400">
              {highestCostRow.grid_import_kw.toFixed(2)} kW
            </p>
          </div>

          <div>
            <p className="text-sm text-slate-400">
              Electricity Cost
            </p>

            <p className="mt-1 font-semibold text-orange-400">
              ₹{highestCostRow.grid_cost_inr.toFixed(2)}
            </p>
          </div>

        </div>

      </div>

    </div>
  )
}

export default ElectricityCostAnalysis