import pandas as pd
import numpy as np

MODES = [
    "cost_saving",
    "battery_life",
    "solar_priority",
    "backup_priority",
    "balanced"
]

BATTERY_CAPACITY = 200
MIN_SOC = 0.20
MAX_SOC = 0.90
MAX_CHARGE_POWER = 50
MAX_DISCHARGE_POWER = 50

TOLERANCE = 0.001

print("\nAPEMA ENERGY MANAGEMENT VALIDATION")
print("=" * 70)

all_modes_passed = True

for mode in MODES:

    print(f"\nVALIDATING MODE: {mode}")
    print("-" * 60)

    file_path = f"results/{mode}_results.csv"
    data = pd.read_csv(file_path)

    checks = {}

    # 1. Power balance
    balance_error = (
        data["grid_import_kw"]
        + data["battery_discharge_kw"]
        + data["solar_kw"]
        - data["solar_curtailment_kw"]
        - data["battery_charge_kw"]
        - data["demand_kw"]
    )

    checks["Power balance"] = (
        np.all(np.abs(balance_error) <= TOLERANCE)
    )

    # 2. Battery SOC limits
    checks["Minimum SOC"] = (
        data["battery_soc"].min() >= MIN_SOC - TOLERANCE
    )

    checks["Maximum SOC"] = (
        data["battery_soc"].max() <= MAX_SOC + TOLERANCE
    )

    # 3. Charging power limit
    checks["Charging power limit"] = (
        data["battery_charge_kw"].max()
        <= MAX_CHARGE_POWER + TOLERANCE
    )

    # 4. Discharging power limit
    checks["Discharging power limit"] = (
        data["battery_discharge_kw"].max()
        <= MAX_DISCHARGE_POWER + TOLERANCE
    )

    # 5. No simultaneous charging and discharging
    simultaneous = (
        (data["battery_charge_kw"] > TOLERANCE)
        & (data["battery_discharge_kw"] > TOLERANCE)
    )

    checks["No simultaneous operation"] = (
        not simultaneous.any()
    )

    # 6. Battery energy and SOC consistency
    expected_soc = (
        data["battery_energy_kwh"] / BATTERY_CAPACITY
    )

    checks["SOC consistency"] = (
        np.all(
            np.abs(expected_soc - data["battery_soc"])
            <= TOLERANCE
        )
    )

    # 7. Terminal SOC target
    terminal_targets = {
        "cost_saving": 0.50,
        "battery_life": 0.50,
        "solar_priority": 0.50,
        "backup_priority": 0.70,
        "balanced": 0.50
    }

    target = terminal_targets[mode]

    checks["Terminal SOC target"] = (
        data["battery_soc"].iloc[-1] >= target - TOLERANCE
    )

    for check_name, passed in checks.items():

        status = "PASS" if passed else "FAIL"

        print(f"{check_name}: {status}")

        if not passed:
            all_modes_passed = False

    print(
        "Final SOC:",
        round(data["battery_soc"].iloc[-1] * 100, 2),
        "%"
    )

print("\n" + "=" * 70)

if all_modes_passed:
    print("RESULT: ALL FIVE MODES PASSED VALIDATION")
else:
    print("RESULT: SOME VALIDATION CHECKS FAILED")

print("APEMA validation completed.")
