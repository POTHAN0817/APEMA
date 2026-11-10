import pandas as pd

FILE = "results/apema_optimization_results.csv"

data = pd.read_csv(FILE)

# System constraints
MAX_CHARGE_KW = 50
MAX_DISCHARGE_KW = 50

MIN_SOC = 0.20
MAX_SOC = 0.90

# Recalculate power balance
data["balance_error_kw"] = (
    data["grid_import_kw"]
    + data["solar_used_kw"]
    + data["battery_discharge_kw"]
    - data["demand_kw"]
    - data["battery_charge_kw"]
)

print("\nAPEMA OPTIMIZATION VALIDATION")
print("--------------------------------")

print("Number of records:", len(data))

print(
    "Maximum power balance error:",
    round(data["balance_error_kw"].abs().max(), 8),
    "kW"
)

print(
    "Minimum battery SOC:",
    round(data["battery_soc"].min() * 100, 2),
    "%"
)

print(
    "Maximum battery SOC:",
    round(data["battery_soc"].max() * 100, 2),
    "%"
)

print(
    "Maximum charging power:",
    round(data["battery_charge_kw"].max(), 2),
    "kW"
)

print(
    "Maximum discharging power:",
    round(data["battery_discharge_kw"].max(), 2),
    "kW"
)

simultaneous_operation = (
    (data["battery_charge_kw"] > 1e-6)
    & (data["battery_discharge_kw"] > 1e-6)
).sum()

print(
    "Simultaneous charge/discharge intervals:",
    simultaneous_operation
)

print(
    "Total electricity cost: ₹",
    round(data["grid_cost_inr"].sum(), 2)
)

print(
    "Final battery SOC:",
    round(data["battery_soc"].iloc[-1] * 100, 2),
    "%"
)

# Validation checks
assert len(data) == 24
assert data["balance_error_kw"].abs().max() < 1e-5
assert data["battery_soc"].min() >= MIN_SOC - 1e-6
assert data["battery_soc"].max() <= MAX_SOC + 1e-6
assert data["battery_charge_kw"].max() <= MAX_CHARGE_KW + 1e-6
assert data["battery_discharge_kw"].max() <= MAX_DISCHARGE_KW + 1e-6
assert simultaneous_operation == 0

print("\nAll operational constraint checks passed.")

if data["battery_soc"].iloc[-1] < 0.50:
    print(
        "WARNING: Final SOC is below initial SOC. "
        "A terminal SOC constraint should be added."
    )