import pandas as pd

from apema_optimizer import APEMAOptimizer
from apema_modes import APEMA_MODES


INPUT_FILE = "data/processed/apema_optimizer_input.csv"

data = pd.read_csv(INPUT_FILE)

summary = []

print("\nAPEMA FIVE-MODE DETAILED COMPARISON")
print("=" * 65)

for mode in APEMA_MODES:

    optimizer = APEMAOptimizer(mode=mode)

    results, objective_value = optimizer.optimize(data)

    # Save individual hourly schedule
    output_file = f"results/{mode}_results.csv"

    results.to_csv(output_file, index=False)

    # Calculate performance metrics
    grid_cost = results["grid_cost_inr"].sum()

    degradation_cost = (
        results["degradation_cost_inr"].sum()
    )

    throughput = (
        results["battery_throughput_kwh"].sum()
    )

    solar_generated = (
        results["solar_kw"].sum()
    )

    solar_used = (
        results["solar_used_kw"].sum()
    )

    solar_utilization = (
        solar_used / solar_generated * 100
        if solar_generated > 0 else 0
    )

    summary.append({
        "mode": mode,
        "grid_cost_inr": grid_cost,
        "degradation_cost_inr": degradation_cost,
        "battery_throughput_kwh": throughput,
        "solar_utilization_percent": solar_utilization,
        "minimum_soc_percent": results["battery_soc"].min() * 100,
        "final_soc_percent": results["battery_soc"].iloc[-1] * 100
    })

    print(f"\nMode: {mode}")
    print(f"Grid cost: ₹{grid_cost:.2f}")
    print(f"Degradation cost: ₹{degradation_cost:.2f}")
    print(f"Battery throughput: {throughput:.2f} kWh")
    print(f"Solar utilization: {solar_utilization:.2f}%")
    print(f"Saved: {output_file}")


summary_df = pd.DataFrame(summary)

summary_df.to_csv(
    "results/apema_mode_comparison.csv",
    index=False
)

print("\nFINAL COMPARISON")
print("=" * 65)
print(summary_df.to_string(index=False))

print("\nAll five detailed schedules saved successfully.")