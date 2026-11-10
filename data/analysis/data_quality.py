import pandas as pd
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "commercial_demand.csv"

# Load dataset
df = pd.read_csv(INPUT_PATH, parse_dates=["timestamp"])

print("\nAPEMA - DATA QUALITY ANALYSIS")
print("==============================")

# 1. Missing values
print("\n1. MISSING VALUES")
print("Missing demand readings:", df["demand"].isna().sum())

# 2. Duplicate timestamps
print("\n2. DUPLICATE TIMESTAMPS")
print("Duplicates:", df["timestamp"].duplicated().sum())

# 3. Zero and negative readings
print("\n3. INVALID READINGS")
print("Zero readings:", (df["demand"] == 0).sum())
print("Negative readings:", (df["demand"] < 0).sum())

# 4. Statistical summary
print("\n4. STATISTICAL SUMMARY")
print(df["demand"].describe().round(2))

# 5. Interquartile range outlier detection
Q1 = df["demand"].quantile(0.25)
Q3 = df["demand"].quantile(0.75)

IQR = Q3 - Q1

lower_limit = Q1 - 1.5 * IQR
upper_limit = Q3 + 1.5 * IQR

outliers = df[
    (df["demand"] < lower_limit) |
    (df["demand"] > upper_limit)
]

print("\n5. OUTLIER ANALYSIS")
print("Lower limit:", round(lower_limit, 2))
print("Upper limit:", round(upper_limit, 2))
print("Detected outliers:", len(outliers))

print("\nHighest detected outliers:")
print(
    outliers.nlargest(10, "demand")[
        ["timestamp", "demand"]
    ].to_string(index=False)
)

# 6. Time interval analysis
time_gaps = df["timestamp"].diff()

print("\n6. TIME INTERVAL ANALYSIS")
print("Intervals longer than one hour:",
      (time_gaps > pd.Timedelta(hours=1)).sum())

print("\nData quality analysis completed.")
