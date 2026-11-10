import joblib
import pandas as pd
from pathlib import Path


def generate_forecast():

    project_root = Path(__file__).resolve().parents[1]

    model_path = (
        project_root
        / "forecasting"
        / "models"
        / "demand_model.pkl"
    )

    data_path = (
        project_root
        / "data"
        / "processed"
        / "commercial_demand.csv"
    )

    output_path = (
        project_root
        / "data"
        / "processed"
        / "demand_forecast_24h.csv"
    )

    model = joblib.load(model_path)

    data = pd.read_csv(data_path)

    data["timestamp"] = pd.to_datetime(data["timestamp"])

    data = data.sort_values("timestamp")

    last_timestamp = data["timestamp"].iloc[-1]

    last_demand = data["demand"].iloc[-1]

    future_timestamps = pd.date_range(
        start=last_timestamp + pd.Timedelta(hours=1),
        periods=24,
        freq="h"
    )

    forecast_data = []

    previous_demand = last_demand

    for timestamp in future_timestamps:

        features = pd.DataFrame([{
            "hour": timestamp.hour,
            "day_of_week": timestamp.day_of_week,
            "month": timestamp.month,
            "previous_hour": previous_demand
        }])

        predicted_demand = model.predict(features)[0]

        forecast_data.append({
            "timestamp": timestamp,
            "predicted_demand": predicted_demand
        })

        previous_demand = predicted_demand

    forecast_df = pd.DataFrame(forecast_data)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    forecast_df.to_csv(output_path, index=False)

    print("\nAPEMA 24-HOUR DEMAND FORECAST")
    print("=============================")

    print(forecast_df.to_string(index=False))

    print("\nAverage predicted demand:",
          round(forecast_df["predicted_demand"].mean(), 3))

    print("Forecast saved to:", output_path)


if __name__ == "__main__":

    generate_forecast()