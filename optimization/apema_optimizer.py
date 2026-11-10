import numpy as np
import pandas as pd

from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.sparse import lil_matrix

from optimization.degradation_settings import DEGRADATION_COST_PER_KWH
from optimization.apema_modes import APEMA_MODES


class APEMAOptimizer:

    def __init__(
        self,
        mode="balanced",
        battery_capacity=200,
        max_charge_power=50,
        max_discharge_power=50,
        min_soc=0.20,
        max_soc=0.90,
        initial_soc=0.50,
        efficiency=0.95,
        time_interval=1,
        terminal_soc=None
    ):

        if mode not in APEMA_MODES:
            raise ValueError(f"Unknown APEMA mode: {mode}")

        self.mode = mode
        self.settings = APEMA_MODES[mode]

        self.battery_capacity = battery_capacity
        self.max_charge_power = max_charge_power
        self.max_discharge_power = max_discharge_power

        self.min_soc = max(
            min_soc,
            self.settings["reserve_soc"]
        )

        self.max_soc = max_soc
        self.initial_soc = initial_soc
        self.efficiency = efficiency
        self.dt = time_interval

        self.degradation_weight = self.settings["degradation_weight"]
        self.solar_weight = self.settings["solar_weight"]

        self.terminal_soc = (
            max(initial_soc, self.settings["terminal_soc"])
            if terminal_soc is None
            else terminal_soc
        )

        if not self.min_soc <= self.initial_soc <= self.max_soc:
            raise ValueError("Initial SOC is outside permitted limits.")

        if not self.min_soc <= self.terminal_soc <= self.max_soc:
            raise ValueError("Terminal SOC is outside permitted limits.")

    def optimize(self, data):

        required_columns = [
            "demand_kw",
            "solar_kw",
            "tariff_inr_per_kwh"
        ]

        for column in required_columns:
            if column not in data.columns:
                raise ValueError(f"Missing column: {column}")

        data = data.copy().reset_index(drop=True)

        n = len(data)

        if n == 0:
            raise ValueError("Input data is empty.")

        demand = data["demand_kw"].to_numpy(dtype=float)
        solar = data["solar_kw"].to_numpy(dtype=float)
        tariff = data["tariff_inr_per_kwh"].to_numpy(dtype=float)

        if not all(
            np.all(np.isfinite(values))
            for values in [demand, solar, tariff]
        ):
            raise ValueError("Input contains invalid numeric values.")

        if np.any(demand < 0) or np.any(solar < 0) or np.any(tariff < 0):
            raise ValueError("Input values cannot be negative.")

        # Variable indices
        grid = np.arange(0, n)
        charge = np.arange(n, 2 * n)
        discharge = np.arange(2 * n, 3 * n)
        curtail = np.arange(3 * n, 4 * n)
        charge_binary = np.arange(4 * n, 5 * n)
        discharge_binary = np.arange(5 * n, 6 * n)
        energy = np.arange(6 * n, 7 * n)

        total_variables = 7 * n

        objective = np.zeros(total_variables)

        objective[grid] = tariff * self.dt

        objective[charge] = (
            DEGRADATION_COST_PER_KWH
            * self.degradation_weight
            * self.dt
        )

        objective[discharge] = (
            DEGRADATION_COST_PER_KWH
            * self.degradation_weight
            * self.dt
        )

        objective[curtail] = 0.01 * self.solar_weight * self.dt

        lower = np.zeros(total_variables)
        upper = np.full(total_variables, np.inf)

        upper[charge] = self.max_charge_power
        upper[discharge] = self.max_discharge_power
        upper[curtail] = solar

        upper[charge_binary] = 1
        upper[discharge_binary] = 1

        lower[energy] = self.min_soc * self.battery_capacity
        upper[energy] = self.max_soc * self.battery_capacity

        integrality = np.zeros(total_variables)
        integrality[charge_binary] = 1
        integrality[discharge_binary] = 1

        rows = []
        row_lower = []
        row_upper = []

        # Power balance
        for t in range(n):

            row = lil_matrix((1, total_variables))

            row[0, grid[t]] = 1
            row[0, discharge[t]] = 1
            row[0, charge[t]] = -1
            row[0, curtail[t]] = -1

            rows.append(row)
            row_lower.append(demand[t] - solar[t])
            row_upper.append(demand[t] - solar[t])

        # Battery energy transitions
        initial_energy = self.initial_soc * self.battery_capacity

        for t in range(n):

            row = lil_matrix((1, total_variables))

            row[0, energy[t]] = 1
            row[0, charge[t]] = -self.efficiency * self.dt
            row[0, discharge[t]] = self.dt / self.efficiency

            if t > 0:
                row[0, energy[t - 1]] = -1
                rhs = 0
            else:
                rhs = initial_energy

            rows.append(row)
            row_lower.append(rhs)
            row_upper.append(rhs)

        # Charging limits
        for t in range(n):

            row = lil_matrix((1, total_variables))

            row[0, charge[t]] = 1
            row[0, charge_binary[t]] = -self.max_charge_power

            rows.append(row)
            row_lower.append(-np.inf)
            row_upper.append(0)

        # Discharging limits
        for t in range(n):

            row = lil_matrix((1, total_variables))

            row[0, discharge[t]] = 1
            row[0, discharge_binary[t]] = -self.max_discharge_power

            rows.append(row)
            row_lower.append(-np.inf)
            row_upper.append(0)

        # No simultaneous charge and discharge
        for t in range(n):

            row = lil_matrix((1, total_variables))

            row[0, charge_binary[t]] = 1
            row[0, discharge_binary[t]] = 1

            rows.append(row)
            row_lower.append(-np.inf)
            row_upper.append(1)

        # Terminal SOC requirement
        row = lil_matrix((1, total_variables))
        row[0, energy[-1]] = 1

        terminal_energy = self.terminal_soc * self.battery_capacity

        rows.append(row)
        row_lower.append(terminal_energy)
        row_upper.append(np.inf)

        matrix = lil_matrix((len(rows), total_variables))

        for i, current_row in enumerate(rows):
            matrix[i, :] = current_row

        constraints = LinearConstraint(
            matrix.tocsr(),
            np.array(row_lower),
            np.array(row_upper)
        )

        result = milp(
            c=objective,
            integrality=integrality,
            bounds=Bounds(lower, upper),
            constraints=constraints
        )

        if not result.success:
            raise RuntimeError(
                f"APEMA optimization failed: {result.message}"
            )

        solution = result.x

        grid_import = solution[grid]
        battery_charge = solution[charge]
        battery_discharge = solution[discharge]
        solar_curtailment = solution[curtail]
        battery_energy = solution[energy]

        battery_soc = battery_energy / self.battery_capacity

        grid_cost = np.sum(grid_import * tariff * self.dt)

        throughput = np.sum(
            (battery_charge + battery_discharge) * self.dt
        )

        degradation_cost = (
            throughput
            * DEGRADATION_COST_PER_KWH
            * self.degradation_weight
        )

        output = data.copy()

        output["grid_import_kw"] = grid_import
        output["battery_charge_kw"] = battery_charge
        output["battery_discharge_kw"] = battery_discharge
        output["solar_curtailment_kw"] = solar_curtailment
        output["battery_energy_kwh"] = battery_energy
        output["battery_soc"] = battery_soc
        output["solar_used_kw"] = solar - solar_curtailment

        output["grid_cost_inr"] = grid_import * tariff * self.dt

        output["battery_throughput_kwh"] = (
            battery_charge + battery_discharge
        ) * self.dt

        output["degradation_cost_inr"] = (
            (battery_charge + battery_discharge)
            * self.dt
            * DEGRADATION_COST_PER_KWH
            * self.degradation_weight
        )

        print("\nAPEMA OPTIMIZATION COMPLETED")
        print("=" * 50)
        print("Operating mode:", self.mode)
        print("Initial SOC:", self.initial_soc * 100, "%")
        print("Minimum SOC:", self.min_soc * 100, "%")
        print("Target terminal SOC:", self.terminal_soc * 100, "%")
        print("Actual final SOC:", round(battery_soc[-1] * 100, 2), "%")
        print("Grid cost: ₹", round(grid_cost, 2))
        print("Battery throughput:", round(throughput, 2), "kWh")
        print("Estimated degradation cost: ₹", round(degradation_cost, 2))

        return output, result.fun


if __name__ == "__main__":

    input_file = "data/processed/apema_optimizer_input.csv"

    data = pd.read_csv(input_file)

    optimizer = APEMAOptimizer(mode="balanced")

    results, objective_value = optimizer.optimize(data)

    results.to_csv(
        "results/apema_optimization_results.csv",
        index=False
    )

    print("\nObjective value:", round(objective_value, 2))
    print("Results saved successfully.")