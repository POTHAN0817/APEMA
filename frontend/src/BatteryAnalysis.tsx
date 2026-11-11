import Plot from "react-plotly.js";

interface BatteryRow {
  timestamp: string;
  battery_charge_kw: number;
  battery_discharge_kw: number;
  battery_soc: number;
}

interface BatteryAnalysisProps {
  data: BatteryRow[];
  capacityKwh?: number;
}

function BatteryAnalysis({
  data,
  capacityKwh = 200,
}: BatteryAnalysisProps) {
  const CYCLE_LIFE = 4000;
  const TIME_STEP_HOURS = 1;

  // Calculate total charging and discharging energy
  const totalCharging = data.reduce(
    (sum, row) =>
      sum + row.battery_charge_kw * TIME_STEP_HOURS,
    0
  );

  const totalDischarging = data.reduce(
    (sum, row) =>
      sum + row.battery_discharge_kw * TIME_STEP_HOURS,
    0
  );

  // Total battery energy throughput
  const totalThroughput = totalCharging + totalDischarging;

  // Equivalent Full Cycles
  const efc = totalThroughput / (2 * capacityKwh);

  // Estimated degradation percentage
  const degradation =
    (efc / CYCLE_LIFE) * 100;

  if (data.length === 0) {
    return (
      <div className="rounded-xl border border-slate-700 bg-slate-900 p-6 text-slate-300">
        Run an optimization to view battery analysis.
      </div>
    );
  }

  return (
    <div className="space-y-6">

      {/* Section heading */}
      <div>
        <h2 className="text-xl font-semibold text-white">
          Battery Charge & Discharge Analysis
        </h2>

        <p className="mt-1 text-sm text-slate-400">
          Hourly battery operation and estimated degradation.
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">

        <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">
            Total Charging Energy
          </p>

          <h3 className="mt-2 text-2xl font-bold text-green-400">
            {totalCharging.toFixed(2)} kWh
          </h3>
        </div>

        <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">
            Total Discharging Energy
          </p>

          <h3 className="mt-2 text-2xl font-bold text-orange-400">
            {totalDischarging.toFixed(2)} kWh
          </h3>
        </div>

        <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">
            Equivalent Full Cycles
          </p>

          <h3 className="mt-2 text-2xl font-bold text-blue-400">
            {efc.toFixed(4)}
          </h3>
        </div>

        <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">
            Estimated Degradation
          </p>

          <h3 className="mt-2 text-2xl font-bold text-purple-400">
            {degradation.toFixed(6)}%
          </h3>
        </div>

      </div>

      {/* Hourly charging and discharging chart */}
      <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">

        <h3 className="mb-4 text-lg font-semibold text-white">
          Hourly Battery Charging & Discharging
        </h3>

        <Plot
          data={[
            {
              x: data.map((row) => row.timestamp),
              y: data.map((row) => row.battery_charge_kw),
              type: "bar",
              name: "Charging Power",
              marker: { color: "#22c55e" },
            },
            {
              x: data.map((row) => row.timestamp),
              y: data.map((row) => row.battery_discharge_kw),
              type: "bar",
              name: "Discharging Power",
              marker: { color: "#f97316" },
            },
          ]}
          layout={{
            autosize: true,
            barmode: "group",
            paper_bgcolor: "rgba(0,0,0,0)",
            plot_bgcolor: "rgba(0,0,0,0)",
            font: { color: "#cbd5e1" },
            xaxis: {
              title: { text: "Time" },
              gridcolor: "#334155",
            },
            yaxis: {
              title: { text: "Power (kW)" },
              gridcolor: "#334155",
              rangemode: "tozero",
            },
            legend: {
              orientation: "h",
              y: 1.15,
            },
            margin: {
              l: 60,
              r: 20,
              t: 35,
              b: 70,
            },
          }}
          config={{ responsive: true }}
          style={{ width: "100%", height: "380px" }}
        />

      </div>

      {/* Battery degradation explanation */}
      <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">

        <h3 className="text-lg font-semibold text-white">
          Battery Degradation Assessment
        </h3>

        <div className="mt-3 space-y-2 text-sm text-slate-400">

          <p>
            Battery Capacity:{" "}
            <span className="text-white">
              {capacityKwh} kWh
            </span>
          </p>

          <p>
            Assumed Cycle Life:{" "}
            <span className="text-white">
              {CYCLE_LIFE} cycles
            </span>
          </p>

          <p>
            Total Energy Throughput:{" "}
            <span className="text-white">
              {totalThroughput.toFixed(2)} kWh
            </span>
          </p>

          <p>
            Estimated Equivalent Full Cycles:{" "}
            <span className="text-white">
              {efc.toFixed(4)}
            </span>
          </p>

          <p>
            Estimated Degradation:{" "}
            <span className="text-purple-400">
              {degradation.toFixed(6)}%
            </span>
          </p>

        </div>

        <p className="mt-4 text-xs text-slate-500">
          Degradation is an illustrative throughput-based estimate,
          not a measured battery State of Health (SOH).
        </p>

      </div>

    </div>
  );
}

export default BatteryAnalysis;