import pandas as pd
import numpy as np

from degradation_settings import DEGRADATION_COST_PER_KWH


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

APEMA_MODES = [
    "cost_saving",
    "battery_life",
    "solar_priority",
    "backup_priority",
    "balanced"
]

BASELINES = [
    "solar_first",
    "price_only",
    "degradation_aware"
]

INITIAL_SOC = 0.50
BATTERY_CAPACITY = 200

# Same illustrative degradation coefficient for all strategies.
DEGRADATION_COST = DEGRADATION_COST_PER_KWH


# --------------------------------------------------
# LOAD AND ANALYZE ONE STRATEGY
# --------------------------------------------------

def analyze_strategy(name, file_path, strategy_type):

    data = pd.read_csv(file_path)

    grid_cost = data["grid_cost_inr"].sum()

    throughput = data["battery_throughput_kwh"].sum()

    if strategy_type == "apema":

        mode_weights = {
            "cost_saving": 0.5,
            "battery_life": 10.0,
            "solar_priority": 1.0,
            "backup_priority": 2.0,
            "balanced": 2.0
        }

        degradation_weight = mode_weights[name]

    else:
        degradation_weight = 1.0

    degradation_cost = (
        throughput
        * DEGRADATION_COST
        * degradation_weight
    )

    final_soc = data["battery_soc"].iloc[-1]

    initial_energy = INITIAL_SOC * BATTERY_CAPACITY

    final_energy = final_soc * BATTERY_CAPACITY

    soc_change_kwh = final_energy - initial_energy

    # Approximate replacement-value adjustment.
    # Positive SOC change is a stored-energy benefit.
    # Negative SOC change is an energy withdrawal.
    soc_adjustment = (
        soc_change_kwh
        * DEGRADATION_COST
    )

    adjusted_cost = (
        grid_cost
        + degradation_cost
        - soc_adjustment
    )

    solar_generated = (
        data["solar_kw"].sum()
    )

    solar_used = (
        data["solar_used_kw"].sum()
        if "solar_used_kw" in data.columns
        else (
            data["solar_kw"].sum()
            - data["solar_curtailment_kw"].sum()
        )
    )

    solar_utilization = (
        solar_used / solar_generated * 100
        if solar_generated > 0
        else 0
    )

    return {
        "strategy": name,
        "strategy_type": strategy_type,
        "grid_cost_inr": grid_cost,
        "degradation_cost_inr": degradation_cost,
        "battery_throughput_kwh": throughput,
        "solar_utilization_percent": solar_utilization,
        "initial_soc_percent": INITIAL_SOC * 100,
        "final_soc_percent": final_soc * 100,
        "soc_change_kwh": soc_change_kwh,
        "soc_adjustment_inr": soc_adjustment,
        "soc_adjusted_cost_inr": adjusted_cost
    }


# --------------------------------------------------
# COMPARE ALL STRATEGIES
# --------------------------------------------------

def main():

    print("\nAPEMA VS BASELINE PERFORMANCE COMPARISON")
    print("=" * 85)

    results = []

    for mode in APEMA_MODES:

        file_path = f"results/{mode}_results.csv"

        result = analyze_strategy(
            mode,
            file_path,
            "apema"
        )

        results.append(result)

    for strategy in BASELINES:

        file_path = f"results/{strategy}_results.csv"

        result = analyze_strategy(
            strategy,
            file_path,
            "baseline"
        )

        results.append(result)

    comparison = pd.DataFrame(results)

    comparison = comparison.sort_values(
        by="soc_adjusted_cost_inr"
    )

    output_file = "results/all_strategy_comparison.csv"

    comparison.to_csv(
        output_file,
        index=False
    )

    display_columns = [
        "strategy",
        "grid_cost_inr",
        "degradation_cost_inr",
        "battery_throughput_kwh",
        "solar_utilization_percent",
        "final_soc_percent",
        "soc_adjusted_cost_inr"
    ]

    print("\nFINAL PERFORMANCE COMPARISON")
    print("=" * 85)

    print(
        comparison[display_columns].round(2).to_string(index=False)
    )

    print("\nResults saved to:", output_file)

    print("\nCOMPARISON COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    main()