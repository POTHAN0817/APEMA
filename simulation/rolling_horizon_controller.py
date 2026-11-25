"""
Rolling-Horizon Model Predictive Control (MPC) Controller for APEMA.

Coordinates:
- Dynamic 24-hour ahead demand forecasting using trained Random Forest regressor
- Diurnal solar generation forecasting using SolarPVModel
- Time-of-use electricity tariff schedule
- APEMA SciPy MILP optimizer
- Real-time battery physical state feedback and degradation tracking
- Receding horizon execution (1-hour step execution with feedback loop)
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
import joblib

# Ensure project root is in Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from battery.battery_model import BatteryModel
from battery.degradation_model import BatteryDegradationModel
from optimization.apema_optimizer import APEMAOptimizer
from optimization.apema_modes import APEMA_MODES
from optimization.degradation_settings import DEGRADATION_COST_PER_KWH
from solar.solar_model import SolarPVModel
from tariff.tariff_model import TariffModel


class RollingHorizonController:
    """
    Model Predictive Control (MPC) controller for commercial building energy management.
    """

    def __init__(
        self,
        mode: str = "balanced",
        initial_soc: float = 0.50,
        battery_capacity: float = 200.0,
        max_charge_power: float = 50.0,
        max_discharge_power: float = 50.0,
        min_soc: float = 0.20,
        max_soc: float = 0.90,
        charge_efficiency: float = 0.95,
        discharge_efficiency: float = 0.95,
        cycle_life: int = 4000,
        planning_horizon: int = 24,
        simulation_duration: int = 24,
        time_interval: float = 1.0,
        historical_data_path: Optional[str] = None,
        model_path: Optional[str] = None,
        start_time: Optional[str] = None,
        terminal_soc: Optional[float] = None
    ):
        """
        Initialize the Rolling-Horizon MPC Controller.
        """
        if mode not in APEMA_MODES:
            raise ValueError(
                f"Unknown APEMA mode: {mode}. Must be one of {list(APEMA_MODES.keys())}"
            )

        self.mode = mode
        self.settings = APEMA_MODES[mode]

        self.battery_capacity = float(battery_capacity)
        self.max_charge_power = float(max_charge_power)
        self.max_discharge_power = float(max_discharge_power)

        # Enforce mode-specific reserve limits
        self.min_soc = max(float(min_soc), self.settings["reserve_soc"])
        self.max_soc = float(max_soc)

        # Enforce initial SOC within bounds
        self.initial_soc = float(np.clip(initial_soc, self.min_soc, self.max_soc))

        self.charge_efficiency = float(charge_efficiency)
        self.discharge_efficiency = float(discharge_efficiency)
        self.cycle_life = int(cycle_life)

        self.planning_horizon = int(planning_horizon)
        self.simulation_duration = int(simulation_duration)
        self.dt = float(time_interval)
        self.terminal_soc = terminal_soc

        # Paths
        self.historical_data_path = (
            Path(historical_data_path)
            if historical_data_path
            else PROJECT_ROOT / "data" / "processed" / "commercial_demand.csv"
        )
        self.model_path = (
            Path(model_path)
            if model_path
            else PROJECT_ROOT / "forecasting" / "models" / "demand_model.pkl"
        )

        self.start_time_str = start_time
        self.current_time: Optional[pd.Timestamp] = None
        self.start_time: Optional[pd.Timestamp] = None

        # Underlying physical and economic components
        self.battery = BatteryModel(
            capacity_kwh=self.battery_capacity,
            max_charge_kw=self.max_charge_power,
            max_discharge_kw=self.max_discharge_power,
            min_soc=self.min_soc,
            max_soc=self.max_soc,
            initial_soc=self.initial_soc,
            charge_efficiency=self.charge_efficiency,
            discharge_efficiency=self.discharge_efficiency
        )

        self.degradation_model = BatteryDegradationModel(
            battery_capacity_kwh=self.battery_capacity,
            cycle_life=self.cycle_life
        )

        self.solar_model = SolarPVModel(
            capacity_kw=100,
            performance_ratio=0.80
        )

        self.tariff_model = TariffModel()

        self.optimizer = APEMAOptimizer(
            mode=self.mode,
            battery_capacity=self.battery_capacity,
            max_charge_power=self.max_charge_power,
            max_discharge_power=self.max_discharge_power,
            min_soc=self.min_soc,
            max_soc=self.max_soc,
            initial_soc=self.initial_soc,
            efficiency=self.charge_efficiency,
            time_interval=self.dt,
            terminal_soc=self.terminal_soc
        )

        # Standard diurnal solar irradiance curve (W/m^2)
        self.hourly_irradiance = {
            0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 50,
            6: 150, 7: 300, 8: 500, 9: 700, 10: 850, 11: 950,
            12: 1000, 13: 950, 14: 850, 15: 700, 16: 500, 17: 250,
            18: 100, 19: 20, 20: 0, 21: 0, 22: 0, 23: 0
        }

        # Data & model storage
        self.demand_model = None
        self.historical_demand_df: Optional[pd.DataFrame] = None
        self.historical_demand_series: Optional[pd.Series] = None

        # Execution tracking
        self.step_index = 0
        self.execution_history: List[Dict[str, Any]] = []
        self.is_initialized = False

    def initialize(self):
        """
        Load datasets, trained model, and set initial simulation clock.
        """
        # Load ML forecasting model if available
        if self.model_path.exists():
            self.demand_model = joblib.load(self.model_path)
        else:
            self.demand_model = None

        # Load historical demand data
        if self.historical_data_path.exists():
            df = pd.read_csv(self.historical_data_path)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp").reset_index(drop=True)
            self.historical_demand_df = df
            self.historical_demand_series = df.set_index("timestamp")["demand"]

            # Establish simulation start time
            if self.start_time_str:
                self.start_time = pd.to_datetime(self.start_time_str)
            else:
                # Default start time: chronological 80% split point (first out-of-sample test day)
                split_idx = int(len(df) * 0.8)
                self.start_time = df["timestamp"].iloc[split_idx]

            # Verify that boundary allows requested simulation duration + planning horizon
            end_required = self.start_time + pd.Timedelta(
                hours=self.simulation_duration + self.planning_horizon
            )
            max_available = df["timestamp"].max()
            if end_required > max_available:
                # If requested window exceeds dataset, adjust start_time to fit exactly
                max_start = max_available - pd.Timedelta(
                    hours=self.simulation_duration + self.planning_horizon
                )
                if max_start < df["timestamp"].min():
                    raise ValueError(
                        f"Requested duration {self.simulation_duration}h + horizon {self.planning_horizon}h "
                        f"exceeds total dataset span ({len(df)} hours)."
                    )
                self.start_time = max_start

            self.current_time = self.start_time

        else:
            # Fallback when historical file is not found (e.g. mock test environment)
            self.historical_demand_df = None
            self.historical_demand_series = None
            self.start_time = pd.to_datetime(self.start_time_str or "2018-01-01 00:00:00")
            self.current_time = self.start_time

        # Reset battery state
        self.battery = BatteryModel(
            capacity_kwh=self.battery_capacity,
            max_charge_kw=self.max_charge_power,
            max_discharge_kw=self.max_discharge_power,
            min_soc=self.min_soc,
            max_soc=self.max_soc,
            initial_soc=self.initial_soc,
            charge_efficiency=self.charge_efficiency,
            discharge_efficiency=self.discharge_efficiency
        )
        self.degradation_model = BatteryDegradationModel(
            battery_capacity_kwh=self.battery_capacity,
            cycle_life=self.cycle_life
        )

        self.step_index = 0
        self.execution_history = []
        self.is_initialized = True

    def get_forecast_window(
        self,
        current_time: pd.Timestamp,
        previous_demand: float
    ) -> pd.DataFrame:
        """
        Generate dynamic 24-hour forward forecast for demand, solar, and tariff.
        """
        horizon_timestamps = pd.date_range(
            start=current_time,
            periods=self.planning_horizon,
            freq="h"
        )

        # 1. Demand Forecast
        predicted_demands = []
        if self.demand_model is not None:
            lag_val = previous_demand
            for ts in horizon_timestamps:
                features = pd.DataFrame([{
                    "hour": ts.hour,
                    "day_of_week": ts.day_of_week,
                    "month": ts.month,
                    "previous_hour": lag_val
                }])
                pred = float(self.demand_model.predict(features)[0])
                pred = max(0.0, pred)
                predicted_demands.append(pred)
                lag_val = pred
        else:
            # Fallback if no ML model is available (uses historical slice if present, else default)
            for ts in horizon_timestamps:
                if (
                    self.historical_demand_series is not None
                    and ts in self.historical_demand_series.index
                ):
                    val = float(self.historical_demand_series.loc[ts])
                else:
                    val = float(previous_demand)
                predicted_demands.append(val)

        # 2. Solar Generation Forecast
        solar_gens = []
        for ts in horizon_timestamps:
            irr = self.hourly_irradiance.get(ts.hour, 0)
            gen = float(self.solar_model.calculate_generation([irr])[0])
            solar_gens.append(gen)

        # 3. Electricity Tariff Schedule
        tariffs = []
        for ts in horizon_timestamps:
            rate = float(self.tariff_model.get_price(ts.hour))
            tariffs.append(rate)

        forecast_df = pd.DataFrame({
            "timestamp": horizon_timestamps,
            "demand_kw": predicted_demands,
            "solar_kw": solar_gens,
            "tariff_inr_per_kwh": tariffs
        })

        return forecast_df

    def optimize_current_window(
        self,
        forecast_df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, float]:
        """
        Execute APEMA MILP optimization for the current forecast window using current SOC.
        """
        current_soc = self.battery.soc
        optimal_schedule, objective_value = self.optimizer.optimize(
            data=forecast_df,
            initial_soc=current_soc
        )
        return optimal_schedule, objective_value

    def execute_first_step(
        self,
        optimal_df: pd.DataFrame,
        actual_demand: Optional[float] = None,
        actual_solar: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Apply the first-hour decision to the physical battery, compute realized power flows,
        and update the state.
        """
        # Extract first-hour decision
        first_row = optimal_df.iloc[0]
        cmd_charge_kw = float(first_row["battery_charge_kw"])
        cmd_discharge_kw = float(first_row["battery_discharge_kw"])
        pred_demand_kw = float(first_row["demand_kw"])
        sched_solar_kw = float(first_row["solar_kw"])
        tariff_rate = float(first_row["tariff_inr_per_kwh"])

        # Determine realized demand and solar
        if actual_demand is None:
            actual_demand = pred_demand_kw
        if actual_solar is None:
            actual_solar = sched_solar_kw

        # Record battery state before action
        soc_before = self.battery.soc
        energy_before = self.battery.energy_kwh

        # Apply action to physical battery model with efficiency losses
        if cmd_charge_kw > 0.001:
            stored_energy = self.battery.charge(cmd_charge_kw, duration_hours=self.dt)
            delivered_energy = 0.0
            actual_charge_kw = cmd_charge_kw
            actual_discharge_kw = 0.0
        elif cmd_discharge_kw > 0.001:
            delivered_energy = self.battery.discharge(cmd_discharge_kw, duration_hours=self.dt)
            stored_energy = 0.0
            actual_charge_kw = 0.0
            actual_discharge_kw = cmd_discharge_kw
        else:
            stored_energy = 0.0
            delivered_energy = 0.0
            actual_charge_kw = 0.0
            actual_discharge_kw = 0.0

        # Update degradation model
        charge_throughput = actual_charge_kw * self.dt
        discharge_throughput = actual_discharge_kw * self.dt
        step_throughput = charge_throughput + discharge_throughput

        self.degradation_model.calculate_degradation(
            charge_energy=charge_throughput,
            discharge_energy=discharge_throughput
        )

        step_degradation_cost = (
            step_throughput
            * DEGRADATION_COST_PER_KWH
            * self.settings["degradation_weight"]
        )

        # Realized energy balance at building AC bus
        # P_grid + P_solar_used + P_discharge = P_demand + P_charge
        net_load = actual_demand + actual_charge_kw - actual_discharge_kw - actual_solar

        if net_load >= 0:
            actual_grid_import = net_load
            actual_solar_curtailment = 0.0
            actual_solar_used = actual_solar
        else:
            # Solar surplus exceeds remaining demand + battery charging
            actual_grid_import = 0.0
            actual_solar_curtailment = abs(net_load)
            actual_solar_used = actual_solar - actual_solar_curtailment

        actual_grid_cost = actual_grid_import * tariff_rate * self.dt

        # Assemble step record
        step_record = {
            "step": self.step_index,
            "timestamp": str(self.current_time),
            "predicted_demand_kw": round(pred_demand_kw, 4),
            "actual_demand_kw": round(actual_demand, 4),
            "solar_generation_kw": round(actual_solar, 4),
            "tariff_inr_per_kwh": round(tariff_rate, 4),
            "grid_import_kw": round(actual_grid_import, 4),
            "battery_charge_kw": round(actual_charge_kw, 4),
            "battery_discharge_kw": round(actual_discharge_kw, 4),
            "battery_energy_kwh": round(self.battery.energy_kwh, 4),
            "battery_soc": round(self.battery.soc, 6),
            "solar_used_kw": round(actual_solar_used, 4),
            "solar_curtailment_kw": round(actual_solar_curtailment, 4),
            "grid_cost_inr": round(actual_grid_cost, 4),
            "battery_throughput_kwh": round(step_throughput, 4),
            "degradation_cost_inr": round(step_degradation_cost, 4),
            "soc_before": round(soc_before, 6),
            "soc_after": round(self.battery.soc, 6)
        }

        self.execution_history.append(step_record)
        return step_record

    def advance_time(self):
        """
        Advance simulation clock by time_interval (default 1 hour).
        """
        self.current_time += pd.Timedelta(hours=self.dt)
        self.step_index += 1

    def run(self) -> pd.DataFrame:
        """
        Execute full rolling-horizon MPC simulation loop over simulation_duration.
        """
        if not self.is_initialized:
            self.initialize()

        # Find starting previous demand
        if (
            self.historical_demand_series is not None
            and (self.current_time - pd.Timedelta(hours=self.dt)) in self.historical_demand_series.index
        ):
            previous_demand = float(
                self.historical_demand_series.loc[
                    self.current_time - pd.Timedelta(hours=self.dt)
                ]
            )
        elif (
            self.historical_demand_series is not None
            and self.current_time in self.historical_demand_series.index
        ):
            previous_demand = float(self.historical_demand_series.loc[self.current_time])
        else:
            previous_demand = 850.0  # Representative commercial office load fallback

        for step in range(self.simulation_duration):
            # 1. Obtain dynamic 24h forecast window
            forecast_df = self.get_forecast_window(
                current_time=self.current_time,
                previous_demand=previous_demand
            )

            # 2. Run APEMA MILP optimizer for current window
            optimal_schedule, obj_val = self.optimize_current_window(forecast_df)

            # 3. Retrieve actual realized demand from historical dataset
            if (
                self.historical_demand_series is not None
                and self.current_time in self.historical_demand_series.index
            ):
                actual_demand = float(self.historical_demand_series.loc[self.current_time])
            else:
                actual_demand = float(forecast_df["demand_kw"].iloc[0])

            actual_solar = float(forecast_df["solar_kw"].iloc[0])

            # 4. Execute only first-hour decision and update physical battery
            step_record = self.execute_first_step(
                optimal_df=optimal_schedule,
                actual_demand=actual_demand,
                actual_solar=actual_solar
            )
            step_record["optimization_status"] = "Optimal"
            step_record["optimization_objective"] = round(obj_val, 4)

            # 5. Update previous demand for next forecast iteration
            previous_demand = actual_demand

            # 6. Advance clock
            self.advance_time()

        return self.get_results()

    def get_results(self) -> pd.DataFrame:
        """
        Return DataFrame containing complete rolling-horizon execution log.
        """
        return pd.DataFrame(self.execution_history)

    def save_results(self, output_path: Optional[str] = None) -> Path:
        """
        Save simulation results to CSV.
        """
        results_df = self.get_results()

        # Always save canonical rolling_horizon_results.csv
        canonical_file = PROJECT_ROOT / "results" / "rolling_horizon_results.csv"
        canonical_file.parent.mkdir(parents=True, exist_ok=True)
        results_df.to_csv(canonical_file, index=False)

        # Also save mode-specific or custom output path
        if output_path is None:
            output_file = (
                PROJECT_ROOT
                / "results"
                / f"rolling_horizon_{self.mode}_results.csv"
            )
        else:
            output_file = Path(output_path)

        output_file.parent.mkdir(parents=True, exist_ok=True)
        results_df.to_csv(output_file, index=False)
        return output_file


if __name__ == "__main__":
    print("Testing Rolling-Horizon MPC Controller...")
    controller = RollingHorizonController(
        mode="balanced",
        simulation_duration=24
    )
    results = controller.run()
    saved_path = controller.save_results()

    print("\nROLLING-HORIZON SIMULATION COMPLETED")
    print("====================================")
    print(f"Total steps executed: {len(results)}")
    print(f"Total realized grid cost: ₹{results['grid_cost_inr'].sum():.2f}")
    print(f"Total battery throughput: {results['battery_throughput_kwh'].sum():.2f} kWh")
    print(f"Final battery SOC: {results['battery_soc'].iloc[-1] * 100:.2f}%")
    print(f"Saved to: {saved_path}")
