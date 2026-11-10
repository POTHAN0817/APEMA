import numpy as np
import pandas as pd
from pathlib import Path


class SolarPVModel:

    def __init__(
        self,
        capacity_kw=100,
        performance_ratio=0.80
    ):
        self.capacity_kw = capacity_kw
        self.performance_ratio = performance_ratio

    def calculate_generation(self, irradiance):
        """
        Estimate solar PV power output.

        irradiance: Solar irradiance in W/m2
        Returns: Estimated PV power in kW
        """

        irradiance = np.asarray(irradiance, dtype=float)

        generation = (
            self.capacity_kw
            * (irradiance / 1000)
            * self.performance_ratio
        )

        generation = np.clip(
            generation,
            0,
            self.capacity_kw
        )

        return generation


if __name__ == "__main__":

    # Illustrative hourly solar irradiance profile
    irradiance = [
        0, 0, 0, 0, 0, 50,
        150, 300, 500, 700, 850, 950,
        1000, 950, 850, 700, 500, 250,
        100, 20, 0, 0, 0, 0
    ]

    solar_model = SolarPVModel(
        capacity_kw=100,
        performance_ratio=0.80
    )

    generation = solar_model.calculate_generation(
        irradiance
    )

    results = pd.DataFrame({
        "hour": range(24),
        "irradiance_w_m2": irradiance,
        "solar_generation_kw": generation
    })

    print("\nAPEMA SOLAR PV GENERATION")
    print("=========================")
    print(results.to_string(index=False))

    print(
        "\nTotal daily solar energy:",
        round(results["solar_generation_kw"].sum(), 2),
        "kWh"
    )