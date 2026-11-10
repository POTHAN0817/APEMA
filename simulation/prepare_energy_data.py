import pandas as pd
from pathlib import Path


def prepare_energy_dataset():

    project_root = Path(__file__).resolve().parents[1]
    data_folder = project_root / "data" / "processed"

    demand = pd.read_csv(data_folder / "demand_forecast_24h.csv")
    solar = pd.read_csv(data_folder / "solar_forecast_24h.csv")
    tariff = pd.read_csv(data_folder / "hourly_tariff.csv")

    demand["timestamp"] = pd.to_datetime(demand["timestamp"])
    solar["timestamp"] = pd.to_datetime(solar["timestamp"])

    demand["hour"] = demand["timestamp"].dt.hour
    solar["hour"] = solar["timestamp"].dt.hour

    combined = demand.merge(
        solar[["hour", "solar_generation_kw"]],
        on="hour",
        how="inner"
    )

    combined = combined.merge(
        tariff,
        on="hour",
        how="inner"
    )

    output_path = data_folder / "combined_energy_data.csv"
    combined.to_csv(output_path, index=False)

    print("\nAPEMA COMBINED ENERGY DATA")
    print("==========================")
    print(combined.to_string(index=False))
    print("\nTotal records:", len(combined))
    print("Missing values:", combined.isna().sum().sum())
    print("Combined dataset saved:", output_path)


if __name__ == "__main__":
    prepare_energy_dataset()
