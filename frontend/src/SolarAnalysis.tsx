import Plot from 'react-plotly.js'

interface SolarRow {
  timestamp: string
  solar_kw: number
  solar_used_kw: number
  solar_curtailment_kw: number
}

interface SolarAnalysisProps {
  data: SolarRow[]
}

function SolarAnalysis({ data }: SolarAnalysisProps) {

  const TIME_STEP_HOURS = 1

  if (data.length === 0) {
    return (
      <div className="rounded-xl border border-slate-700 bg-slate-900 p-6 text-slate-300">
        Run an optimization to view solar energy analysis.
      </div>
    )
  }

  const totalSolarGenerated = data.reduce(
    (sum, row) => sum + row.solar_kw * TIME_STEP_HOURS,
    0
  )

  const totalSolarUsed = data.reduce(
    (sum, row) => sum + row.solar_used_kw * TIME_STEP_HOURS,
    0
  )

  const totalSolarCurtailed = data.reduce(
    (sum, row) => sum + row.solar_curtailment_kw * TIME_STEP_HOURS,
    0
  )

  const utilization =
    totalSolarGenerated > 0
      ? (totalSolarUsed / totalSolarGenerated) * 100
      : 0

  const curtailmentPercentage =
    totalSolarGenerated > 0
      ? (totalSolarCurtailed / totalSolarGenerated) * 100
      : 0

  return (
    <div className="space-y-6">

      {/* Heading */}
      <div>
        <h2 className="text-xl font-semibold text-white">
          Solar Energy Utilization Analysis
        </h2>

        <p className="mt-1 text-sm text-slate-400">
          Analysis of solar generation, utilization and energy curtailment.
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">

        <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">
            Total Solar Generated
          </p>

          <h3 className="mt-2 text-2xl font-bold text-yellow-400">
            {totalSolarGenerated.toFixed(2)} kWh
          </h3>
        </div>

        <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">
            Solar Energy Utilized
          </p>

          <h3 className="mt-2 text-2xl font-bold text-green-400">
            {totalSolarUsed.toFixed(2)} kWh
          </h3>
        </div>

        <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">
            Solar Curtailment
          </p>

          <h3 className="mt-2 text-2xl font-bold text-orange-400">
            {totalSolarCurtailed.toFixed(2)} kWh
          </h3>
        </div>

        <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">
            Solar Utilization
          </p>

          <h3 className="mt-2 text-2xl font-bold text-cyan-400">
            {utilization.toFixed(2)}%
          </h3>
        </div>

      </div>

      {/* Solar Utilization Chart */}
      <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">

        <h3 className="mb-4 text-lg font-semibold text-white">
          Solar Generation vs Utilization
        </h3>

        <Plot
          data={[
            {
              x: data.map((row) => row.timestamp),
              y: data.map((row) => row.solar_kw),
              type: 'bar',
              name: 'Solar Generation',
              marker: { color: '#eab308' },
            },
            {
              x: data.map((row) => row.timestamp),
              y: data.map((row) => row.solar_used_kw),
              type: 'bar',
              name: 'Solar Utilized',
              marker: { color: '#22c55e' },
            },
          ]}
          layout={{
            autosize: true,
            barmode: 'group',
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#cbd5e1' },
            xaxis: {
              title: { text: 'Time' },
              gridcolor: '#334155',
            },
            yaxis: {
              title: { text: 'Power (kW)' },
              gridcolor: '#334155',
              rangemode: 'tozero',
            },
            margin: { l: 65, r: 20, t: 30, b: 70 },
            legend: { orientation: 'h', y: 1.15 },
          }}
          config={{ responsive: true }}
          style={{ width: '100%', height: '350px' }}
        />

      </div>

      {/* Solar Energy Distribution */}
      <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">

        <h3 className="mb-4 text-lg font-semibold text-white">
          Solar Energy Distribution
        </h3>

        <Plot
          data={[
            {
              labels: ['Solar Utilized', 'Solar Curtailed'],
              values: [totalSolarUsed, totalSolarCurtailed],
              type: 'pie',
              hole: 0.55,
              marker: {
                colors: ['#22c55e', '#f97316'],
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
            font: { color: '#cbd5e1' },
            showlegend: true,
            margin: { l: 20, r: 20, t: 20, b: 20 },
          }}
          config={{ responsive: true }}
          style={{ width: '100%', height: '350px' }}
        />

      </div>

      {/* Solar Curtailment Assessment */}
      <div className="rounded-xl border border-orange-500/30 bg-slate-900 p-5">

        <h3 className="text-lg font-semibold text-white">
          Solar Energy Performance Assessment
        </h3>

        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">

          <div>
            <p className="text-sm text-slate-400">
              Solar Utilization
            </p>

            <p className="mt-1 text-xl font-bold text-green-400">
              {utilization.toFixed(2)}%
            </p>
          </div>

          <div>
            <p className="text-sm text-slate-400">
              Curtailment Percentage
            </p>

            <p className="mt-1 text-xl font-bold text-orange-400">
              {curtailmentPercentage.toFixed(2)}%
            </p>
          </div>

          <div>
            <p className="text-sm text-slate-400">
              Solar Energy Balance
            </p>

            <p className="mt-1 text-xl font-bold text-cyan-400">
              {(totalSolarUsed + totalSolarCurtailed).toFixed(2)} kWh
            </p>
          </div>

        </div>

        <p className="mt-4 text-xs text-slate-500">
          Solar generation is based on the project's simulated solar profile.
          These values are simulation results, not measured PV production.
        </p>

      </div>

    </div>
  )
}

export default SolarAnalysis