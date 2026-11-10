import pandas as pd
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]

ELECTRICITY_PATH = (
    PROJECT_ROOT.parent
    / "BDG2_Download"
    / "building-data-genome-project-2"
    / "data"
    / "meters"
    / "cleaned"
    / "electricity_cleaned.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "commercial_demand.csv"
)

# Selected commercial building
BUILDING_ID = "Hog_office_Byron"

print("Loading BDG2 electricity dataset...")

# Load electricity data
df = pd.read_csv(ELECTRICITY_PATH)

# Check building availability
if BUILDING_ID not in df.columns:
    raise ValueError(f"{BUILDING_ID} not found in electricity dataset.")

# Extract timestamp and building demand
demand = df[["timestamp", BUILDING_ID]].copy()

# Convert timestamp
demand["timestamp"] = pd.to_datetime(demand["timestamp"])

# Rename column
demand = demand.rename(
    columns={BUILDING_ID: "demand"}
)

# Sort chronologically
demand = demand.sort_values("timestamp")

# Check missing values
print("\nOriginal records:", len(demand))
print("Missing readings:", demand["demand"].isna().sum())

# Remove missing readings for the initial dataset
demand = demand.dropna(subset=["demand"])

# Save processed dataset
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
demand.to_csv(OUTPUT_PATH, index=False)

print("\nDATA PREPARATION COMPLETE")
print("=========================")
print("Selected building:", BUILDING_ID)
print("Valid records:", len(demand))
print("First timestamp:", demand["timestamp"].min())
print("Last timestamp:", demand["timestamp"].max())
print("Average reading:", demand["demand"].mean())
print("Maximum reading:", demand["demand"].max())
print("Minimum reading:", demand["demand"].min())
print("\nSaved to:", OUTPUT_PATH)