import pandas as pd

modes = [
    "cost_saving",
    "battery_life",
    "solar_priority",
    "backup_priority",
    "balanced"
]

print("\nAPEMA HOURLY BATTERY SCHEDULE ANALYSIS")
print("=" * 75)

for mode in modes:

    file = f"results/{mode}_results.csv"

    data = pd.read_csv(file)

    charging_hours = (
        data["battery_charge_kw"] > 0.001
    ).sum()

    discharging_hours = (
        data["battery_discharge_kw"] > 0.001
    ).sum()

    idle_hours = (
        (
            data["battery_charge_kw"] <= 0.001
        )
        &
        (
            data["battery_discharge_kw"] <= 0.001
        )
    ).sum()

    average_soc = (
        data["battery_soc"].mean() * 100
    )

    print(f"\nMODE: {mode}")

    print("Charging hours:", charging_hours)
    print("Discharging hours:", discharging_hours)
    print("Idle hours:", idle_hours)

    print("Average battery SOC:", round(average_soc, 2), "%")

    print("\nHourly decisions:")

    print(
        data[
            [
                "timestamp",
                "battery_charge_kw",
                "battery_discharge_kw",
                "battery_soc",
                "grid_import_kw"
            ]
        ].to_string(index=False)
    )

print("\nHourly schedule analysis completed.")