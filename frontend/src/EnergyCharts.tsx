import Plot from 'react-plotly.js'

interface EnergyRow {
  timestamp: string
  demand_kw: number
  solar_kw: number
  grid_import_kw: number
  battery_charge_kw: number
  battery_discharge_kw: number
  battery_soc: number
}

interface Props {
  data: EnergyRow[]
}

const layout = {
  paper_bgcolor: '#0f172a',
  plot_bgcolor: '#0f172a',
  font: { color: '#cbd5e1' },
  margin: { t: 45, r: 20, b: 55, l: 65 },
  xaxis: {
    gridcolor: '#334155',
    title: { text: 'Hour' },
  },
  yaxis: {
    gridcolor: '#334155',
  },
  autosize: true,
  height: 340,
}

export default function EnergyCharts({ data }: Props) {
  const hours = data.map((row) =>
    new Date(row.timestamp).toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    })
  )

  const commonConfig = {
    responsive: true,
    displayModeBar: false,
  }

  return (
    <section className="grid grid-cols-1 gap-6 xl:grid-cols-2">

      <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
        <h3 className="mb-4 font-semibold">
          Building Demand vs Solar Generation
        </h3>

        <Plot
          data={[
            {
              x: hours,
              y: data.map((r) => r.demand_kw),
              type: 'scatter',
              mode: 'lines',
              name: 'Demand',
              line: { color: '#22d3ee', width: 3 },
            },
            {
              x: hours,
              y: data.map((r) => r.solar_kw),
              type: 'scatter',
              mode: 'lines',
              name: 'Solar',
              line: { color: '#fbbf24', width: 3 },
            },
          ]}
          layout={{
            ...layout,
            title: { text: 'Power Profile (kW)' },
            yaxis: {
              ...layout.yaxis,
              title: { text: 'Power (kW)' },
            },
          }}
          config={commonConfig}
          useResizeHandler
          style={{ width: '100%' }}
        />
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
        <h3 className="mb-4 font-semibold">
          Grid Electricity Import
        </h3>

        <Plot
          data={[
            {
              x: hours,
              y: data.map((r) => r.grid_import_kw),
              type: 'bar',
              name: 'Grid Import',
              marker: { color: '#818cf8' },
            },
          ]}
          layout={{
            ...layout,
            title: { text: 'Grid Import (kW)' },
            yaxis: {
              ...layout.yaxis,
              title: { text: 'Power (kW)' },
            },
          }}
          config={commonConfig}
          useResizeHandler
          style={{ width: '100%' }}
        />
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
        <h3 className="mb-4 font-semibold">
          Battery Charging and Discharging
        </h3>

        <Plot
          data={[
            {
              x: hours,
              y: data.map((r) => r.battery_charge_kw),
              type: 'bar',
              name: 'Charging',
              marker: { color: '#34d399' },
            },
            {
              x: hours,
              y: data.map((r) => -r.battery_discharge_kw),
              type: 'bar',
              name: 'Discharging',
              marker: { color: '#fb7185' },
            },
          ]}
          layout={{
            ...layout,
            title: { text: 'Battery Power (kW)' },
            barmode: 'relative',
            yaxis: {
              ...layout.yaxis,
              title: { text: 'Power (kW)' },
            },
          }}
          config={commonConfig}
          useResizeHandler
          style={{ width: '100%' }}
        />
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
        <h3 className="mb-4 font-semibold">
          Battery State of Charge
        </h3>

        <Plot
          data={[
            {
              x: hours,
              y: data.map((r) => r.battery_soc * 100),
              type: 'scatter',
              mode: 'lines+markers',
              name: 'Battery SOC',
              line: { color: '#a78bfa', width: 3 },
            },
          ]}
          layout={{
            ...layout,
            title: { text: 'Battery SOC (%)' },
            yaxis: {
              ...layout.yaxis,
              title: { text: 'SOC (%)' },
              range: [0, 100],
            },
          }}
          config={commonConfig}
          useResizeHandler
          style={{ width: '100%' }}
        />
      </div>

    </section>
  )
}