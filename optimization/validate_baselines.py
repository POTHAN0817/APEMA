import pandas as pd
import numpy as np

STRATEGIES = [
    "solar_first",
    "price_only",
    "degradation_aware"
]

BATTERY_CAPACITY = 200
MIN_SOC = 0.20
MAX_SOC = 0.90
MAX_CHARGE_POWER = 50
MAX_DISCHARGE_POWER = 50

TOLERANCE = 0.001

print("\nBASELINE STRATEGY VALIDATION")
print("=" * 70)

all_passed = True

for strategy in STRATEGIES:

    print(f"\nVALIDATING: {strategy}")
    print("-" * 60)

    file_path = f"results/{strategy}_results.csv"
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

    checks["Power balance"] = np.all(
        np.abs(balance_error) <= TOLERANCE
    )

    # 2. Minimum and maximum SOC
    checks["Minimum SOC"] = (
        data["battery_soc"].min()
        >= MIN_SOC - TOLERANCE
    )

    checks["Maximum SOC"] = (
        data["battery_soc"].max()
        <= MAX_SOC + TOLERANCE
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

    # 6. SOC and battery energy consistency
    expected_soc = (
        data["battery_energy_kwh"] / BATTERY_CAPACITY
    )

    checks["SOC consistency"] = np.all(
        np.abs(
            expected_soc - data["battery_soc"]
        ) <= TOLERANCE
    )

    # 7. Battery energy transition
    previous_energy = np.concatenate((
        [0.50 * BATTERY_CAPACITY],
        data["battery_energy_kwh"].to_numpy()[:-1]
    ))

    expected_energy = (
        previous_energy
        + data["battery_charge_kw"].to_numpy() * 0.95
        - data["battery_discharge_kw"].to_numpy() / 0.95
    )

    checks["Energy transition"] = np.all(
        np.abs(
            expected_energy
            - data["battery_energy_kwh"].to_numpy()
        ) <= TOLERANCE
    )

    for name, passed in checks.items():

        print(
            f"{name}: {'PASS' if passed else 'FAIL'}"
        )

        if not passed:
            all_passed = False

    print(
        "Final SOC:",
        round(data["battery_soc"].iloc[-1] * 100, 2),
        "%"
    )

print("\n" + "=" * 70)

if all_passed:
    print("RESULT: ALL BASELINE STRATEGIES PASSED")
else:
    print("RESULT: SOME BASELINE CHECKS FAILED")

print("Baseline validation completed.")