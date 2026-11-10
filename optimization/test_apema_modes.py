from apema_modes import APEMA_MODES

print("APEMA MODE CONFIGURATION TEST")
print("--------------------------------")

expected_modes = [
    "cost_saving",
    "battery_life",
    "solar_priority",
    "backup_priority",
    "balanced"
]

for mode in expected_modes:

    assert mode in APEMA_MODES

    settings = APEMA_MODES[mode]

    assert settings["degradation_weight"] >= 0
    assert settings["solar_weight"] >= 0
    assert 0 <= settings["reserve_soc"] <= 1

    print(
        f"{mode}: "
        f"Degradation={settings['degradation_weight']}, "
        f"Solar={settings['solar_weight']}, "
        f"Reserve={settings['reserve_soc'] * 100:.0f}%"
    )

assert len(APEMA_MODES) == 5

print("\nAll five APEMA modes passed validation.")