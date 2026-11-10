import numpy as np
import pandas as pd


class BaselineStrategies:

    def __init__(
        self,
        battery_capacity=200,
        max_charge_power=50,
        max_discharge_power=50,
        min_soc=0.20,
        max_soc=0.90,
        initial_soc=0.50,
        efficiency=0.95,
        time_interval=1
    ):

        self.capacity = battery_capacity
        self.max_charge = max_charge_power
        self.max_discharge = max_discharge_power
        self.min_soc = min_soc
        self.max_soc = max_soc
        self.initial_soc = initial_soc
        self.efficiency = efficiency
        self.dt = time_interval

    def run(self, data, strategy="solar_first"):

        data = data.copy().reset_index(drop=True)

        required = [
            "demand_kw",
            "solar_kw",
            "tariff_inr_per_kwh"
        ]

        for column in required:
            if column not in data.columns:
                raise ValueError(f"Missing column: {column}")

        if strategy not in [
            "solar_first",
            "price_only",
            "degradation_aware"
        ]:
            raise ValueError("Unknown baseline strategy.")

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

        n = len(data)

        charge = np.zeros(n)
        discharge = np.zeros(n)
        grid = np.zeros(n)
        solar_curtailment = np.zeros(n)
        energy = np.zeros(n)
        soc = np.zeros(n)

        current_energy = self.initial_soc * self.capacity

        # Identify cheapest and most expensive tariff periods.
        cheap_threshold = np.quantile(tariff, 0.25)
        expensive_threshold = np.quantile(tariff, 0.75)

        for t in range(n):

            available_solar = min(solar[t], demand[t])
            remaining_demand = demand[t] - available_solar

            # Solar surplus, if any, can charge the battery.
            solar_surplus = max(0, solar[t] - demand[t])

            available_capacity = max(
                0,
                self.max_soc * self.capacity - current_energy
            )

            solar_charge = min(
                self.max_charge,
                solar_surplus / self.efficiency,
                available_capacity / (self.efficiency * self.dt)
            )

            if strategy == "solar_first":

                charge[t] = solar_charge

                remaining_capacity = max(
                    0,
                    self.max_soc * self.capacity
                    - current_energy
                    - solar_charge * self.efficiency * self.dt
                )

                if (
                    remaining_demand > 0
                    and current_energy
                    > self.min_soc * self.capacity
                    and tariff[t] >= expensive_threshold
                ):

                    discharge[t] = min(
                        self.max_discharge,
                        remaining_demand,
                        (current_energy - self.min_soc * self.capacity)
                        * self.efficiency / self.dt
                    )

            elif strategy == "price_only":

                if tariff[t] <= cheap_threshold:

                    charge[t] = min(
                        self.max_charge,
                        max(
                            0,
                            (
                                self.max_soc * self.capacity
                                - current_energy
                            ) / (self.efficiency * self.dt)
                        )
                    )

                elif tariff[t] >= expensive_threshold:

                    discharge[t] = min(
                        self.max_discharge,
                        remaining_demand,
                        max(
                            0,
                            (
                                current_energy
                                - self.min_soc * self.capacity
                            ) * self.efficiency / self.dt
                        )
                    )

            elif strategy == "degradation_aware":

                if (
                    solar_surplus > 0
                    and current_energy < self.max_soc * self.capacity
                ):

                    charge[t] = solar_charge

                elif (
                    tariff[t] >= expensive_threshold
                    and current_energy
                    > self.min_soc * self.capacity
                ):

                    # Use only a limited portion of battery capacity.
                    discharge[t] = min(
                        self.max_discharge * 0.5,
                        remaining_demand,
                        max(
                            0,
                            (
                                current_energy
                                - self.min_soc * self.capacity
                            ) * self.efficiency / self.dt
                        )
                    )

            # Enforce battery energy limits.
            charge_energy = (
                charge[t] * self.efficiency * self.dt
            )

            discharge_energy = (
                discharge[t] * self.dt / self.efficiency
            )

            current_energy += charge_energy - discharge_energy

            current_energy = np.clip(
                current_energy,
                self.min_soc * self.capacity,
                self.max_soc * self.capacity
            )

            # Grid supplies all remaining demand.
            grid[t] = (
                demand[t]
                + charge[t]
                - discharge[t]
                - solar[t]
                + solar_curtailment[t]
            )

            grid[t] = max(0, grid[t])

            energy[t] = current_energy
            soc[t] = current_energy / self.capacity

        output = data.copy()

        output["grid_import_kw"] = grid
        output["battery_charge_kw"] = charge
        output["battery_discharge_kw"] = discharge
        output["solar_curtailment_kw"] = solar_curtailment
        output["battery_energy_kwh"] = energy
        output["battery_soc"] = soc

        output["grid_cost_inr"] = (
            grid * tariff * self.dt
        )

        output["battery_throughput_kwh"] = (
            charge + discharge
        ) * self.dt

        return output


if __name__ == "__main__":

    input_file = "data/processed/apema_optimizer_input.csv"

    data = pd.read_csv(input_file)

    baseline = BaselineStrategies()

    strategies = [
        "solar_first",
        "price_only",
        "degradation_aware"
    ]

    print("\nBASELINE STRATEGY TEST")
    print("=" * 60)

    for strategy in strategies:

        result = baseline.run(data, strategy)

        print(f"\nStrategy: {strategy}")
        print(
            "Grid cost: ₹",
            round(result["grid_cost_inr"].sum(), 2)
        )

        print(
            "Battery throughput:",
            round(result["battery_throughput_kwh"].sum(), 2),
            "kWh"
        )

        print(
            "Final SOC:",
            round(result["battery_soc"].iloc[-1] * 100, 2),
            "%"
        )

        result.to_csv(
            f"results/{strategy}_results.csv",
            index=False
        )

        print("Results saved.")