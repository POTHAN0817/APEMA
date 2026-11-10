import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import joblib

class DemandForecaster:

    def __init__(self):

        project_root = Path(__file__).resolve().parents[1]

        file_path = (
            project_root
            / "data"
            / "processed"
            / "commercial_demand.csv"
        )

        self.data = pd.read_csv(file_path)

        self.data["timestamp"] = pd.to_datetime(
            self.data["timestamp"]
        )

        self.data = self.data.sort_values("timestamp")

        self.demand_column = "demand"

    def prepare_data(self):

        self.data["hour"] = self.data["timestamp"].dt.hour

        self.data["day_of_week"] = (
            self.data["timestamp"].dt.day_of_week
        )

        self.data["month"] = self.data["timestamp"].dt.month

        self.data["previous_hour"] = (
            self.data[self.demand_column].shift(1)
        )

        self.data = self.data.dropna().copy()

        features = [
            "hour",
            "day_of_week",
            "month",
            "previous_hour"
        ]

        X = self.data[features]
        y = self.data[self.demand_column]

        return X, y

    def train_and_evaluate(self):

        X, y = self.prepare_data()

        split = int(len(X) * 0.8)

        X_train = X.iloc[:split]
        X_test = X.iloc[split:]

        y_train = y.iloc[:split]
        y_test = y.iloc[split:]

        model = RandomForestRegressor(
            n_estimators=100,
            random_state=42,
            n_jobs=-1
        )

        model.fit(X_train, y_train)
        project_root = Path(__file__).resolve().parents[1]

        model_directory = project_root / "forecasting" / "models"
        model_directory.mkdir(parents=True, exist_ok=True)

        model_path = model_directory / "demand_model.pkl"

        joblib.dump(model, model_path)

        print("Forecasting model saved:", model_path)

        predictions = model.predict(X_test)

        mae = mean_absolute_error(
            y_test,
            predictions
        )

        print("\nAPEMA DEMAND FORECASTING")
        print("========================")

        print("Training records:", len(X_train))
        print("Testing records:", len(X_test))

        print("Mean Absolute Error:", round(mae, 3))

        return model, mae


if __name__ == "__main__":

    forecaster = DemandForecaster()

    forecaster.train_and_evaluate()