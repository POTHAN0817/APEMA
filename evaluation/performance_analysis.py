import os
import pandas as pd
import matplotlib.pyplot as plt

# Create output directory
os.makedirs("results/plots", exist_ok=True)

# Load comparison results
data = pd.read_csv("results/all_strategy_comparison.csv")

# Short display names
data["display_name"] = data["strategy"].str.replace(
    "_", " ", regex=False
).str.title()

# --------------------------------------------------
# GRAPH 1: GRID ELECTRICITY COST
# --------------------------------------------------

plt.figure(figsize=(12, 6))

plt.bar(
    data["display_name"],
    data["grid_cost_inr"]
)

plt.title("Grid Electricity Cost Comparison")
plt.xlabel("Energy Management Strategy")
plt.ylabel("Grid Cost (INR)")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()

plt.savefig("results/plots/grid_cost_comparison.png", dpi=300)
plt.close()


# --------------------------------------------------
# GRAPH 2: BATTERY THROUGHPUT
# --------------------------------------------------

plt.figure(figsize=(12, 6))

plt.bar(
    data["display_name"],
    data["battery_throughput_kwh"]
)

plt.title("Battery Throughput Comparison")
plt.xlabel("Energy Management Strategy")
plt.ylabel("Battery Throughput (kWh)")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()

plt.savefig("results/plots/battery_throughput.png", dpi=300)
plt.close()


# --------------------------------------------------
# GRAPH 3: BATTERY DEGRADATION COST
# --------------------------------------------------

plt.figure(figsize=(12, 6))

plt.bar(
    data["display_name"],
    data["degradation_cost_inr"]
)

plt.title("Estimated Battery Degradation Cost")
plt.xlabel("Energy Management Strategy")
plt.ylabel("Estimated Degradation Cost (INR)")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()

plt.savefig("results/plots/degradation_comparison.png", dpi=300)
plt.close()


# --------------------------------------------------
# GRAPH 4: SOLAR UTILIZATION
# --------------------------------------------------

plt.figure(figsize=(12, 6))

plt.bar(
    data["display_name"],
    data["solar_utilization_percent"]
)

plt.title("Solar Energy Utilization Comparison")
plt.xlabel("Energy Management Strategy")
plt.ylabel("Solar Utilization (%)")
plt.ylim(0, 105)
plt.xticks(rotation=45, ha="right")
plt.tight_layout()

plt.savefig("results/plots/solar_utilization.png", dpi=300)
plt.close()


# --------------------------------------------------
# GRAPH 5: FINAL BATTERY SOC
# --------------------------------------------------

plt.figure(figsize=(12, 6))

plt.bar(
    data["display_name"],
    data["final_soc_percent"]
)

plt.title("Final Battery State of Charge")
plt.xlabel("Energy Management Strategy")
plt.ylabel("Final Battery SOC (%)")
plt.ylim(0, 100)
plt.xticks(rotation=45, ha="right")
plt.tight_layout()

plt.savefig("results/plots/final_soc_comparison.png", dpi=300)
plt.close()


# --------------------------------------------------
# SUMMARY
# --------------------------------------------------

print("\nAPEMA PERFORMANCE ANALYSIS")
print("=" * 65)

print("Strategies analyzed:", len(data))

print("\nGenerated graphs:")

graphs = [
    "grid_cost_comparison.png",
    "battery_throughput.png",
    "degradation_comparison.png",
    "solar_utilization.png",
    "final_soc_comparison.png"
]

for graph in graphs:
    print("Saved: results/plots/" + graph)

print("\nPerformance analysis completed successfully.")