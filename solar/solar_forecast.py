import pandas as pd
import numpy as np
from pathlib import Path

from solar_model import SolarPVModel


def generate_solar_forecast():

    project_root = Path(__file__).resolve().parents[1]

    output_path = (
        project_root
        / "data"
        / "processed"
        / "solar_forecast_24h.csv"
    )

    # Illustrative hourly solar irradiance (W/m²)
    irradiance = np.array([
        0, 0, 0, 0, 0, 50,
        150, 300, 500, 700,
        850, 950, 1000, 950,
        850, 700, 500, 250,
        100, 20, 0, 0, 0, 0
    ])

    solar_model = SolarPVModel(
        capacity_kw=100,
        performance_ratio=0.80
    )

    generation = solar_model.calculate_generation(
        irradiance
    )

    timestamps = pd.date_range(
        start="2018-01-01 00:00:00",
        periods=24,
        freq="h"
    )

    forecast = pd.DataFrame({
        "timestamp": timestamps,
        "irradiance_w_per_m2": irradiance,
        "solar_generation_kw": generation
    })

    forecast.to_csv(output_path, index=False)

    print("\nAPEMA SOLAR FORECAST")
    print("====================")

    print(forecast.to_string(index=False))

    print(
        "\nPeak solar generation:",
        round(forecast["solar_generation_kw"].max(), 2),
        "kW"
    )

    print(
        "Total daily solar energy:",
        round(forecast["solar_generation_kw"].sum(), 2),
        "kWh"
    )

    print("\nSolar forecast saved:", output_path)


if __name__ == "__main__":

    generate_solar_forecast()