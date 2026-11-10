import pandas as pd
from pathlib import Path


class TariffModel:

    def __init__(self):

        # Illustrative time-of-use tariff (₹/kWh)
        self.tariff_rates = {
            0: 4.0,
            1: 4.0,
            2: 4.0,
            3: 4.0,
            4: 4.0,
            5: 4.0,
            6: 5.0,
            7: 5.0,
            8: 6.0,
            9: 6.0,
            10: 6.0,
            11: 6.0,
            12: 6.0,
            13: 6.0,
            14: 6.0,
            15: 7.0,
            16: 7.0,
            17: 8.0,
            18: 8.0,
            19: 8.0,
            20: 7.0,
            21: 6.0,
            22: 5.0,
            23: 4.0
        }

    def get_price(self, hour):

        if hour not in self.tariff_rates:
            raise ValueError("Hour must be between 0 and 23.")

        return self.tariff_rates[hour]

    def calculate_cost(self, energy_kwh, hour):

        if energy_kwh < 0:
            raise ValueError("Energy cannot be negative.")

        price = self.get_price(hour)

        return energy_kwh * price

    def generate_daily_tariff(self):

        data = []

        for hour in range(24):

            price = self.get_price(hour)

            data.append({
                "hour": hour,
                "tariff_inr_per_kwh": price
            })

        return pd.DataFrame(data)


if __name__ == "__main__":

    tariff = TariffModel()

    print("\nAPEMA ELECTRICITY TARIFF MODEL")
    print("==============================")

    daily_tariff = tariff.generate_daily_tariff()

    print(daily_tariff.to_string(index=False))

    print("\nCOST CALCULATION")

    energy = 10
    hour = 18

    cost = tariff.calculate_cost(energy, hour)

    print("Energy consumption:", energy, "kWh")
    print("Hour:", hour)
    print("Electricity price:", tariff.get_price(hour), "₹/kWh")
    print("Total electricity cost:", cost, "₹")

    print("\nMinimum tariff:",
          min(tariff.tariff_rates.values()), "₹/kWh")

    print("Maximum tariff:",
          max(tariff.tariff_rates.values()), "₹/kWh")
              # Save daily tariff dataset

    from pathlib import Path

    project_root = Path(__file__).resolve().parents[1]

    output_path = (
        project_root
        / "data"
        / "processed"
        / "hourly_tariff.csv"
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    daily_tariff.to_csv(output_path, index=False)

    print("\nDaily tariff dataset saved successfully.")
    print("File location:", output_path)

    print("\nTariff model executed successfully.")