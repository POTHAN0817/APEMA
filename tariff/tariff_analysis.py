import pandas as pd
from pathlib import Path


class TariffAnalysis:

    def __init__(self):
        project_root = Path(__file__).resolve().parents[1]

        file_path = (
            project_root
            / "data"
            / "processed"
            / "hourly_tariff.csv"
        )

        self.tariff_data = pd.read_csv(file_path)

    def get_cheapest_hours(self, count=5):
        return self.tariff_data.nsmallest(
            count, "tariff_inr_per_kwh"
        )

    def get_expensive_hours(self, count=5):
        return self.tariff_data.nlargest(
            count, "tariff_inr_per_kwh"
        )

    def display_analysis(self):

        print("\nAPEMA TARIFF ANALYSIS")
        print("=====================")

        print("\nFive Cheapest Hours:")
        print(
            self.get_cheapest_hours().to_string(index=False)
        )

        print("\nFive Most Expensive Hours:")
        print(
            self.get_expensive_hours().to_string(index=False)
        )


if __name__ == "__main__":

    analysis = TariffAnalysis()
    analysis.display_analysis()