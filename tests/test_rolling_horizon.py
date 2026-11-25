import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulation.rolling_horizon_controller import RollingHorizonController
from optimization.apema_modes import APEMA_MODES


def test_controller_initialization():
    """Test 1: Controller initialization and default attributes."""
    controller = RollingHorizonController(
        mode="balanced",
        initial_soc=0.50,
        battery_capacity=200.0,
        planning_horizon=24,
        simulation_duration=24
    )
    controller.initialize()

    assert controller.mode == "balanced"
    assert controller.battery.capacity_kwh == 200.0
    assert controller.battery.soc == 0.50
    assert controller.battery.energy_kwh == 100.0
    assert controller.planning_horizon == 24
    assert controller.simulation_duration == 24
    assert controller.step_index == 0
    assert len(controller.execution_history) == 0
    assert controller.is_initialized is True


def test_invalid_mode_initialization():
    """Test invalid operating mode raises ValueError."""
    with pytest.raises(ValueError, match="Unknown APEMA mode"):
        RollingHorizonController(mode="invalid_mode")


def test_forecast_window_generation():
    """Test 2: Forecast window generation structure and valid ranges."""
    controller = RollingHorizonController(mode="balanced")
    controller.initialize()

    current_time = pd.Timestamp("2017-09-01 00:00:00")
    forecast_df = controller.get_forecast_window(
        current_time=current_time,
        previous_demand=900.0
    )

    assert len(forecast_df) == 24
    expected_cols = ["timestamp", "demand_kw", "solar_kw", "tariff_inr_per_kwh"]
    for col in expected_cols:
        assert col in forecast_df.columns

    # Verify no NaN or negative values
    assert not forecast_df.isnull().any().any()
    assert (forecast_df["demand_kw"] >= 0).all()
    assert (forecast_df["solar_kw"] >= 0).all()
    assert (forecast_df["tariff_inr_per_kwh"] >= 0).all()
    assert forecast_df["timestamp"].iloc[0] == current_time
    assert forecast_df["timestamp"].iloc[-1] == current_time + pd.Timedelta(hours=23)


def test_forecast_window_advancement():
    """Test 3: Forecast window advancement across steps."""
    controller = RollingHorizonController(
        mode="balanced",
        simulation_duration=3
    )
    controller.initialize()

    initial_time = controller.current_time
    controller.advance_time()
    assert controller.current_time == initial_time + pd.Timedelta(hours=1)
    assert controller.step_index == 1

    controller.advance_time()
    assert controller.current_time == initial_time + pd.Timedelta(hours=2)
    assert controller.step_index == 2


def test_dynamic_initial_soc_passed_to_optimizer():
    """Test 4: Optimizer receives dynamic current battery SOC."""
    controller = RollingHorizonController(mode="balanced", simulation_duration=3)
    controller.initialize()

    # Artificially alter battery SOC
    controller.battery.soc = 0.75
    controller.battery.energy_kwh = 150.0

    forecast_df = controller.get_forecast_window(controller.current_time, 900.0)
    optimal_df, obj = controller.optimize_current_window(forecast_df)

    assert controller.optimizer.initial_soc == pytest.approx(0.75, abs=1e-5)
    assert len(optimal_df) == 24


def test_only_first_control_action_executed():
    """Test 5: Only first-hour decision is executed on physical battery."""
    controller = RollingHorizonController(mode="balanced")
    controller.initialize()

    forecast_df = controller.get_forecast_window(controller.current_time, 900.0)
    optimal_df, _ = controller.optimize_current_window(forecast_df)

    expected_charge = float(optimal_df["battery_charge_kw"].iloc[0])
    expected_discharge = float(optimal_df["battery_discharge_kw"].iloc[0])

    step_record = controller.execute_first_step(optimal_df)

    assert step_record["battery_charge_kw"] == pytest.approx(expected_charge, abs=1e-4)
    assert step_record["battery_discharge_kw"] == pytest.approx(expected_discharge, abs=1e-4)
    assert len(controller.execution_history) == 1


def test_battery_soc_updates_correctly():
    """Test 6: Battery physical state updates with efficiency losses."""
    controller = RollingHorizonController(
        mode="cost_saving",
        initial_soc=0.50,
        battery_capacity=200.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95
    )
    controller.initialize()

    # Create synthetic optimal schedule with 50 kW charge at step 0
    synthetic_optimal = pd.DataFrame([{
        "battery_charge_kw": 50.0,
        "battery_discharge_kw": 0.0,
        "demand_kw": 800.0,
        "solar_kw": 0.0,
        "tariff_inr_per_kwh": 4.0
    }])

    initial_energy = controller.battery.energy_kwh
    controller.execute_first_step(synthetic_optimal)

    expected_stored = 50.0 * 1.0 * 0.95  # 47.5 kWh
    expected_energy = initial_energy + expected_stored
    expected_soc = expected_energy / 200.0

    assert controller.battery.energy_kwh == pytest.approx(expected_energy, abs=1e-4)
    assert controller.battery.soc == pytest.approx(expected_soc, abs=1e-4)


def test_soc_remains_within_configured_limits():
    """Test 7: SOC stays within configured min and max limits during execution."""
    controller = RollingHorizonController(
        mode="cost_saving",
        initial_soc=0.50,
        simulation_duration=12
    )
    results = controller.run()

    tol = 1e-4
    assert (results["battery_soc"] >= controller.min_soc - tol).all()
    assert (results["battery_soc"] <= controller.max_soc + tol).all()


def test_battery_power_limits_and_no_simultaneous_operation():
    """Tests 8, 9, 10: Battery charging & discharging power limits and mutual exclusion."""
    controller = RollingHorizonController(
        mode="balanced",
        simulation_duration=12,
        max_charge_power=50.0,
        max_discharge_power=50.0
    )
    results = controller.run()

    tol = 1e-4
    # Power limits
    assert (results["battery_charge_kw"] >= -tol).all()
    assert (results["battery_charge_kw"] <= 50.0 + tol).all()
    assert (results["battery_discharge_kw"] >= -tol).all()
    assert (results["battery_discharge_kw"] <= 50.0 + tol).all()

    # Mutual exclusion (no simultaneous charge and discharge)
    simultaneous = (
        (results["battery_charge_kw"] > 0.001)
        & (results["battery_discharge_kw"] > 0.001)
    )
    assert not simultaneous.any()


def test_power_balance_for_executed_hours():
    """Test 11: Realized power balance at building bus."""
    controller = RollingHorizonController(
        mode="balanced",
        simulation_duration=12
    )
    results = controller.run()

    # P_grid + P_solar_used + P_dis = P_demand + P_ch
    lhs = (
        results["grid_import_kw"]
        + results["solar_used_kw"]
        + results["battery_discharge_kw"]
    )
    rhs = (
        results["actual_demand_kw"]
        + results["battery_charge_kw"]
    )

    diff = np.abs(lhs - rhs)
    assert (diff <= 1e-3).all()


def test_optimization_failure_handling():
    """Test 12: Optimizer failure handling on empty or corrupted input."""
    controller = RollingHorizonController(mode="balanced")
    controller.initialize()

    # Corrupt forecast dataframe with NaN
    corrupted_df = pd.DataFrame({
        "timestamp": pd.date_range("2018-01-01", periods=24, freq="h"),
        "demand_kw": [np.nan] * 24,
        "solar_kw": [0.0] * 24,
        "tariff_inr_per_kwh": [4.0] * 24
    })

    with pytest.raises(ValueError):
        controller.optimize_current_window(corrupted_df)


def test_boundary_handling_exceeding_dataset():
    """Test 13: End-of-simulation boundary handling."""
    # Attempting to start at the very last timestamp of dataset with 24h duration + 24h horizon
    controller = RollingHorizonController(
        mode="balanced",
        start_time="2017-12-31 23:00:00",
        simulation_duration=24
    )
    controller.initialize()
    # It should automatically adjust start_time to fit dataset
    max_allowed_start = controller.historical_demand_df["timestamp"].max() - pd.Timedelta(hours=48)
    assert controller.start_time <= max_allowed_start


def test_results_csv_generation(tmp_path):
    """Test 14: Results CSV file generation."""
    controller = RollingHorizonController(
        mode="balanced",
        simulation_duration=6
    )
    controller.run()

    output_csv = tmp_path / "test_rolling_results.csv"
    controller.save_results(output_path=str(output_csv))

    assert output_csv.exists()
    df = pd.read_csv(output_csv)
    assert len(df) == 6
    assert "battery_soc" in df.columns
    assert "grid_import_kw" in df.columns
    assert "actual_demand_kw" in df.columns
    assert "predicted_demand_kw" in df.columns


@pytest.mark.parametrize("mode_name", list(APEMA_MODES.keys()))
def test_all_five_apema_modes(mode_name):
    """Test 15: Run rolling-horizon execution for all five APEMA modes."""
    controller = RollingHorizonController(
        mode=mode_name,
        simulation_duration=4
    )
    results = controller.run()

    assert len(results) == 4
    assert (results["battery_soc"] >= controller.min_soc - 1e-4).all()
    assert (results["battery_soc"] <= controller.max_soc + 1e-4).all()
    assert (results["battery_throughput_kwh"] >= 0).all()

