import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "commercial_demand.csv"
OUTPUT_DIR = PROJECT_ROOT / "results" / "plots"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load demand data
df = pd.read_csv(INPUT_PATH, parse_dates=["timestamp"])

# Plot electricity demand over time
plt.figure(figsize=(15, 5))
plt.plot(df["timestamp"], df["demand"], linewidth=0.5)

plt.title("Commercial Building Electricity Demand (2016–2017)")
plt.xlabel("Date")
plt.ylabel("Demand (original dataset units)")
plt.grid(True)
plt.tight_layout()

# Save chart
output_file = OUTPUT_DIR / "demand_overview.png"
plt.savefig(output_file, dpi=300)

plt.show()

print("Chart saved to:", output_file)

# ---------------------------------
# Daily and hourly demand analysis
# ---------------------------------

df["hour"] = df["timestamp"].dt.hour
df["date"] = df["timestamp"].dt.date

# Average demand by hour of day
hourly_demand = df.groupby("hour")["demand"].mean()

plt.figure(figsize=(12, 5))
hourly_demand.plot(marker="o")

plt.title("Average Electricity Demand by Hour")
plt.xlabel("Hour of Day")
plt.ylabel("Average Demand (original dataset units)")
plt.xticks(range(24))
plt.grid(True)
plt.tight_layout()

plt.savefig(OUTPUT_DIR / "hourly_demand_pattern.png", dpi=300)
plt.show()

# Average demand by day
daily_demand = df.groupby("date")["demand"].mean()

plt.figure(figsize=(15, 5))
daily_demand.plot()

plt.title("Daily Average Electricity Demand")
plt.xlabel("Date")
plt.ylabel("Average Demand (original dataset units)")
plt.grid(True)
plt.tight_layout()

plt.savefig(OUTPUT_DIR / "daily_demand_pattern.png", dpi=300)
plt.show()

print("Hourly and daily demand analysis completed.")

# ==========================================
# STEP 20: DAILY DEMAND ANALYSIS
# ==========================================

# Extract date from timestamp
df["date"] = df["timestamp"].dt.date

# Calculate daily average demand
daily_demand = df.groupby("date")["demand"].mean()

# Calculate daily statistics
print("\nDAILY DEMAND ANALYSIS")
print("=====================")

print("\nAverage daily demand:", round(daily_demand.mean(), 2))
print("Maximum daily average:", round(daily_demand.max(), 2))
print("Minimum daily average:", round(daily_demand.min(), 2))

print("\nDate with highest average demand:", daily_demand.idxmax())
print("Date with lowest average demand:", daily_demand.idxmin())

# Plot daily demand
plt.figure(figsize=(15, 5))

daily_demand.plot(linewidth=0.8)

plt.title("Daily Average Commercial Building Electricity Demand")
plt.xlabel("Date")
plt.ylabel("Average Demand (original dataset units)")
plt.grid(True)
plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "daily_demand_analysis.png",
    dpi=300
)

plt.show()

print("\nDaily demand analysis completed successfully.")

# ==========================================
# STEP 21: WEEKLY DEMAND ANALYSIS
# ==========================================

# Extract day of week
df["day_of_week"] = df["timestamp"].dt.day_name()

# Set correct weekday order
weekday_order = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
]

# Calculate average demand for each weekday
weekly_demand = (
    df.groupby("day_of_week")["demand"]
    .mean()
    .reindex(weekday_order)
)

# Display results
print("\nWEEKLY DEMAND ANALYSIS")
print("======================")

print("\nAverage demand by weekday:")
print(weekly_demand.round(2))

print("\nHighest demand weekday:", weekly_demand.idxmax())
print("Lowest demand weekday:", weekly_demand.idxmin())

# Plot weekly demand
plt.figure(figsize=(10, 5))

weekly_demand.plot(kind="bar", rot=0)

plt.title("Average Electricity Demand by Day of Week")
plt.xlabel("Day of Week")
plt.ylabel("Average Demand (original dataset units)")
plt.grid(axis="y")
plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "weekly_demand_analysis.png",
    dpi=300
)

plt.show()

print("\nWeekly demand analysis completed successfully.")

# ==========================================
# STEP 22: MONTHLY DEMAND ANALYSIS
# ==========================================

# Extract month and year
df["month"] = df["timestamp"].dt.month
df["year"] = df["timestamp"].dt.year

# Calculate average demand for each month
monthly_demand = df.groupby("month")["demand"].mean()

month_names = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]

monthly_demand.index = month_names

print("\nMONTHLY DEMAND ANALYSIS")
print("=======================")

print("\nAverage demand by month:")
print(monthly_demand.round(2))

print("\nHighest demand month:", monthly_demand.idxmax())
print("Lowest demand month:", monthly_demand.idxmin())

# Plot monthly demand
plt.figure(figsize=(12, 5))

monthly_demand.plot(kind="bar", rot=0)

plt.title("Average Electricity Demand by Month (2016–2017)")
plt.xlabel("Month")
plt.ylabel("Average Demand (original dataset units)")
plt.grid(axis="y")
plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "monthly_demand_analysis.png",
    dpi=300
)

plt.show()

print("\nMonthly demand analysis completed successfully.")

# ==========================================
# STEP 23: PEAK DEMAND ANALYSIS
# ==========================================

# Sort demand readings from highest to lowest
peak_demand = df.nlargest(10, "demand")[
    ["timestamp", "demand"]
]

print("\nTOP 10 PEAK DEMAND READINGS")
print("===========================")
print(peak_demand.to_string(index=False))

# Calculate 95th percentile
peak_threshold = df["demand"].quantile(0.95)

print("\n95th Percentile Demand:", round(peak_threshold, 2))

# Identify high-demand periods
high_demand = df[df["demand"] >= peak_threshold]

print("Number of high-demand readings:", len(high_demand))

# Plot peak demand readings
plt.figure(figsize=(15, 5))

plt.plot(
    df["timestamp"],
    df["demand"],
    linewidth=0.5,
    label="Demand"
)

plt.axhline(
    peak_threshold,
    linestyle="--",
    label="95th Percentile Threshold"
)

plt.title("Commercial Building Peak Demand Analysis")
plt.xlabel("Date")
plt.ylabel("Demand (original dataset units)")
plt.legend()
plt.grid(True)
plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "peak_demand_analysis.png",
    dpi=300
)

plt.show()

print("\nPeak demand analysis completed successfully.")