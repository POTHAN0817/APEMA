import pandas as pd

# Load the combined energy dataset
data = pd.read_csv(
    "data/processed/combined_energy_data.csv"
)

# Simulation assumptions
SOLAR_CAPACITY_KW = 100
BATTERY_CAPACITY_KWH = 200
BATTERY_POWER_KW = 50
TIME_INTERVAL_HOURS = 1

# Convert hourly energy demand into average power
data["demand_kw"] = (
    data["predicted_demand"] / TIME_INTERVAL_HOURS
)

# Calculate system sizing indicators
average_demand = data["demand_kw"].mean()
peak_demand = data["demand_kw"].max()

average_solar = data["solar_generation_kw"].mean()
peak_solar = data["solar_generation_kw"].max()

solar_peak_coverage = (
    SOLAR_CAPACITY_KW / peak_demand
) * 100

battery_power_coverage = (
    BATTERY_POWER_KW / peak_demand
) * 100

battery_duration = (
    BATTERY_CAPACITY_KWH / BATTERY_POWER_KW
)

print("\nAPEMA SYSTEM SIZING CHECK")
print("--------------------------")

print(f"Average demand: {average_demand:.2f} kW")
print(f"Peak demand: {peak_demand:.2f} kW")

print(f"Average solar generation: {average_solar:.2f} kW")
print(f"Peak solar generation: {peak_solar:.2f} kW")

print(f"Solar peak coverage: {solar_peak_coverage:.2f}%")
print(f"Battery power coverage: {battery_power_coverage:.2f}%")

print(f"Battery capacity: {BATTERY_CAPACITY_KWH} kWh")
print(f"Battery power: {BATTERY_POWER_KW} kW")
print(f"Nominal battery duration: {battery_duration:.2f} hours")

print("\nINTERPRETATION")
print("--------------------------")
print("The solar and battery system will serve as")
print("partial energy resources for the office building.")
print("The grid will supply the remaining demand.")