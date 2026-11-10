APEMA_MODES = {
    "cost_saving": {
        "description": "Prioritize electricity cost reduction",
        "degradation_weight": 0.5,
        "solar_weight": 1.0,
        "reserve_soc": 0.20,
        "terminal_soc": 0.50
    },

    "battery_life": {
        "description": "Minimize battery cycling and degradation",
        "degradation_weight": 10.0,
        "solar_weight": 1.0,
        "reserve_soc": 0.50,
        "terminal_soc": 0.50
    },

    "solar_priority": {
        "description": "Maximize solar energy utilization",
        "degradation_weight": 1.0,
        "solar_weight": 5.0,
        "reserve_soc": 0.20,
        "terminal_soc": 0.50
    },

    "backup_priority": {
        "description": "Preserve battery energy for backup",
        "degradation_weight": 2.0,
        "solar_weight": 1.0,
        "reserve_soc": 0.50,
        "terminal_soc": 0.70
    },

    "balanced": {
        "description": "Balance cost, solar and battery life",
        "degradation_weight": 2.0,
        "solar_weight": 2.0,
        "reserve_soc": 0.40,
        "terminal_soc": 0.50
    }
}


if __name__ == "__main__":
    print("\nAPEMA OPERATING MODES")
    print("=" * 60)

    for mode, settings in APEMA_MODES.items():
        print(f"\nMode: {mode}")
        for key, value in settings.items():
            print(f"{key}: {value}")