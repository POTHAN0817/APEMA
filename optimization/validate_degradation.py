import pandas as pd

FILE = "results/apema_optimization_results.csv"

data = pd.read_csv(FILE)

BATTERY_CAPACITY = 200
MIN_SOC = 0.20
MAX_SOC = 0.90
MAX_POWER = 50

print("\nAPEMA DEGRADATION VALIDATION")
print("--------------------------------")

print("Records:", len(data))

print(
    "Total grid cost: ₹",
    round(data["grid_cost_inr"].sum(), 2)
)

print(
    "Total degradation cost: ₹",
    round(data["degradation_cost_inr"].sum(), 2)
)

print(
    "Total battery throughput:",
    round(data["battery_throughput_kwh"].sum(), 2),
    "kWh"
)

print(
    "Minimum SOC:",
    round(data["battery_soc"].min() * 100, 2),
    "%"
)

print(
    "Maximum SOC:",
    round(data["battery_soc"].max() * 100, 2),
    "%"
)

print(
    "Final SOC:",
    round(data["battery_soc"].iloc[-1] * 100, 2),
    "%"
)

print(
    "Maximum charge power:",
    round(data["battery_charge_kw"].max(), 2),
    "kW"
)

print(
    "Maximum discharge power:",
    round(data["battery_discharge_kw"].max(), 2),
    "kW"
)

# Check simultaneous operation
simultaneous = (
    (data["battery_charge_kw"] > 1e-6)
    & (data["battery_discharge_kw"] > 1e-6)
).sum()

print("Simultaneous operation intervals:", simultaneous)

# Validation
assert len(data) == 24
assert data["battery_soc"].min() >= MIN_SOC - 1e-6
assert data["battery_soc"].max() <= MAX_SOC + 1e-6
assert data["battery_charge_kw"].max() <= MAX_POWER + 1e-6
assert data["battery_discharge_kw"].max() <= MAX_POWER + 1e-6
assert simultaneous == 0
assert abs(data["battery_soc"].iloc[-1] - 0.50) < 1e-6
assert (data["battery_throughput_kwh"] >= 0).all()
assert (data["degradation_cost_inr"] >= 0).all()

print("\nAll degradation-aware validation checks passed.")