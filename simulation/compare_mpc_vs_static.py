"""
Comparative Performance Benchmark:
Rolling-Horizon MPC vs. Static 24-Hour APEMA Optimization and Heuristic Baselines.
"""

import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulation.rolling_horizon_controller import RollingHorizonController
from optimization.apema_optimizer import APEMAOptimizer
from optimization.apema_modes import APEMA_MODES
from optimization.baseline_strategies import BaselineStrategies
from optimization.degradation_settings import DEGRADATION_COST_PER_KWH


def run_benchmark():
    print("\nAPEMA PHASE 8: ROLLING-HORIZON MPC BENCHMARK")
    print("=" * 80)

    # Standardized 24-hour evaluation window from the out-of-sample test split
    START_TIME = "2017-09-01 00:00:00"
    SIMULATION_DURATION = 24
    INITIAL_SOC = 0.50

    results = []

    # 1. Run Rolling-Horizon MPC for all 5 modes
    print("\n--- Running Rolling-Horizon MPC (5 Modes) ---")
    for mode in APEMA_MODES:
        t0 = time.time()
        controller = RollingHorizonController(
            mode=mode,
            initial_soc=INITIAL_SOC,
            start_time=START_TIME,
            simulation_duration=SIMULATION_DURATION
        )
        mpc_res = controller.run()
        elapsed = time.time() - t0

        # Save individual rolling CSV
        out_file = controller.save_results()

        grid_cost = float(mpc_res["grid_cost_inr"].sum())
        throughput = float(mpc_res["battery_throughput_kwh"].sum())
        degradation_cost = float(mpc_res["degradation_cost_inr"].sum())
        solar_gen = float(mpc_res["solar_generation_kw"].sum())
        solar_used = float(mpc_res["solar_used_kw"].sum())
        solar_util = (solar_used / solar_gen * 100) if solar_gen > 0 else 0.0
        final_soc = float(mpc_res["battery_soc"].iloc[-1] * 100)
        peak_grid = float(mpc_res["grid_import_kw"].max())

        print(f"MPC [{mode:15s}]: Grid Cost=₹{grid_cost:.2f}, Throughput={throughput:.2f} kWh, "
              f"Final SOC={final_soc:.1f}%, Runtime={elapsed:.2f}s")

        results.append({
            "strategy": f"mpc_{mode}",
            "display_name": f"MPC ({mode.replace('_', ' ').title()})",
            "strategy_type": "rolling_horizon_mpc",
            "grid_cost_inr": grid_cost,
            "battery_throughput_kwh": throughput,
            "degradation_cost_inr": degradation_cost,
            "solar_utilization_percent": solar_util,
            "final_soc_percent": final_soc,
            "peak_grid_kw": peak_grid,
            "runtime_seconds": elapsed
        })

    # Prepare historical benchmark window dataset for static & baselines
    ctrl_ref = RollingHorizonController(start_time=START_TIME, simulation_duration=SIMULATION_DURATION)
    ctrl_ref.initialize()
    eval_timestamps = pd.date_range(start=pd.Timestamp(START_TIME), periods=SIMULATION_DURATION, freq="h")
    realized_demand = [ctrl_ref.historical_demand_series.loc[ts] for ts in eval_timestamps]
    solar_gens = [ctrl_ref.solar_model.calculate_generation([ctrl_ref.hourly_irradiance.get(ts.hour, 0)])[0] for ts in eval_timestamps]
    tariffs = [ctrl_ref.tariff_model.get_price(ts.hour) for ts in eval_timestamps]

    eval_df = pd.DataFrame({
        "timestamp": eval_timestamps,
        "demand_kw": realized_demand,
        "solar_kw": solar_gens,
        "tariff_inr_per_kwh": tariffs
    })

    # 2. Run Static 24-Hour APEMA Optimization (Balanced and Cost Saving)
    print("\n--- Running Static 24-Hour Optimization (Perfect Horizon Reference) ---")
    for mode in ["cost_saving", "balanced"]:
        t0 = time.time()
        optimizer = APEMAOptimizer(mode=mode, initial_soc=INITIAL_SOC)
        static_res, _ = optimizer.optimize(eval_df)
        elapsed = time.time() - t0

        grid_cost = float(static_res["grid_cost_inr"].sum())
        throughput = float(static_res["battery_throughput_kwh"].sum())
        degradation_cost = float(static_res["degradation_cost_inr"].sum())
        solar_gen = float(static_res["solar_kw"].sum())
        solar_used = float(static_res["solar_used_kw"].sum())
        solar_util = (solar_used / solar_gen * 100) if solar_gen > 0 else 0.0
        final_soc = float(static_res["battery_soc"].iloc[-1] * 100)
        peak_grid = float(static_res["grid_import_kw"].max())

        print(f"Static [{mode:15s}]: Grid Cost=₹{grid_cost:.2f}, Throughput={throughput:.2f} kWh, "
              f"Final SOC={final_soc:.1f}%, Runtime={elapsed:.2f}s")

        results.append({
            "strategy": f"static_{mode}",
            "display_name": f"Static ({mode.replace('_', ' ').title()})",
            "strategy_type": "static_optimization",
            "grid_cost_inr": grid_cost,
            "battery_throughput_kwh": throughput,
            "degradation_cost_inr": degradation_cost,
            "solar_utilization_percent": solar_util,
            "final_soc_percent": final_soc,
            "peak_grid_kw": peak_grid,
            "runtime_seconds": elapsed
        })

    # 3. Run Baseline Strategies (Solar First, Price Only, Degradation Aware)
    print("\n--- Running Baseline Strategies ---")
    baselines = ["solar_first", "price_only", "degradation_aware"]
    baseline_runner = BaselineStrategies(initial_soc=INITIAL_SOC)

    for strat in baselines:
        t0 = time.time()
        base_res = baseline_runner.run(eval_df, strategy=strat)
        elapsed = time.time() - t0

        grid_cost = float(base_res["grid_cost_inr"].sum())
        throughput = float(base_res["battery_throughput_kwh"].sum())
        degradation_cost = float(throughput * DEGRADATION_COST_PER_KWH)
        solar_gen = float(base_res["solar_kw"].sum())
        solar_used = float((base_res["solar_kw"] - base_res["solar_curtailment_kw"]).sum())
        solar_util = (solar_used / solar_gen * 100) if solar_gen > 0 else 0.0
        final_soc = float(base_res["battery_soc"].iloc[-1] * 100)
        peak_grid = float(base_res["grid_import_kw"].max())

        print(f"Baseline [{strat:15s}]: Grid Cost=₹{grid_cost:.2f}, Throughput={throughput:.2f} kWh, "
              f"Final SOC={final_soc:.1f}%, Runtime={elapsed:.2f}s")

        results.append({
            "strategy": f"baseline_{strat}",
            "display_name": f"Baseline ({strat.replace('_', ' ').title()})",
            "strategy_type": "baseline",
            "grid_cost_inr": grid_cost,
            "battery_throughput_kwh": throughput,
            "degradation_cost_inr": degradation_cost,
            "solar_utilization_percent": solar_util,
            "final_soc_percent": final_soc,
            "peak_grid_kw": peak_grid,
            "runtime_seconds": elapsed
        })

    # Aggregate results into comparison DataFrame
    comparison_df = pd.DataFrame(results)
    out_csv = PROJECT_ROOT / "results" / "mpc_vs_static_comparison.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    comparison_df.to_csv(out_csv, index=False)

    print("\nBENCHMARK RESULTS SUMMARY")
    print("=" * 80)
    cols = ["display_name", "grid_cost_inr", "battery_throughput_kwh", "degradation_cost_inr", "final_soc_percent", "runtime_seconds"]
    print(comparison_df[cols].round(2).to_string(index=False))
    print(f"\nSaved comparison table: {out_csv}")

    # Plot comparison bar charts
    plot_dir = PROJECT_ROOT / "results" / "plots"
    plot_dir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 1. Grid Cost
    axes[0, 0].bar(comparison_df["display_name"], comparison_df["grid_cost_inr"], color="#06b6d4")
    axes[0, 0].set_title("Total Grid Electricity Cost (₹)")
    axes[0, 0].set_ylabel("Cost (INR)")
    axes[0, 0].tick_params(axis="x", rotation=45)

    # 2. Battery Throughput
    axes[0, 1].bar(comparison_df["display_name"], comparison_df["battery_throughput_kwh"], color="#8b5cf6")
    axes[0, 1].set_title("Battery Throughput (kWh)")
    axes[0, 1].set_ylabel("Throughput (kWh)")
    axes[0, 1].tick_params(axis="x", rotation=45)

    # 3. Final SOC
    axes[1, 0].bar(comparison_df["display_name"], comparison_df["final_soc_percent"], color="#10b981")
    axes[1, 0].set_title("Final Battery SOC (%)")
    axes[1, 0].set_ylabel("SOC (%)")
    axes[1, 0].set_ylim(0, 100)
    axes[1, 0].tick_params(axis="x", rotation=45)

    # 4. Runtime
    axes[1, 1].bar(comparison_df["display_name"], comparison_df["runtime_seconds"], color="#f59e0b")
    axes[1, 1].set_title("Execution Runtime (Seconds)")
    axes[1, 1].set_ylabel("Time (s)")
    axes[1, 1].tick_params(axis="x", rotation=45)

    plt.tight_layout()
    plot_file = plot_dir / "mpc_vs_static_comparison.png"
    plt.savefig(plot_file, dpi=300)
    plt.close()
    print(f"Saved comparison figure: {plot_file}")

    return comparison_df


if __name__ == "__main__":
    run_benchmark()

