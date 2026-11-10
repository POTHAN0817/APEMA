import pandas as pd

INPUT_FILE = "data/processed/combined_energy_data.csv"
OUTPUT_FILE = "data/processed/apema_optimizer_input.csv"

INTERVAL_HOURS = 1.0

data = pd.read_csv(INPUT_FILE)

data["timestamp"] = pd.to_datetime(data["timestamp"])

# Explicit hourly energy demand
data["demand_kwh"] = data["predicted_demand"]

# Convert hourly energy to average power
data["demand_kw"] = (
    data["demand_kwh"] / INTERVAL_HOURS
)

# Keep solar generation in kW
data["solar_kw"] = data["solar_generation_kw"]

# Keep electricity tariff
data["tariff_inr_per_kwh"] = (
    data["tariff_inr_per_kwh"]
)

# Select optimizer input columns
optimizer_data = data[
    [
        "timestamp",
        "demand_kwh",
        "demand_kw",
        "solar_kw",
        "tariff_inr_per_kwh",
    ]
].copy()

optimizer_data.to_csv(OUTPUT_FILE, index=False)

print("APEMA OPTIMIZER INPUT CREATED")
print("--------------------------------")
print("Records:", len(optimizer_data))
print("Columns:", optimizer_data.columns.tolist())
print("Missing values:", optimizer_data.isnull().sum().sum())

print("\nFirst five records:")
print(optimizer_data.head().to_string(index=False))

print("\nFile saved:", OUTPUT_FILE)