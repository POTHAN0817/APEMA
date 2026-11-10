# APEMA battery degradation settings

BATTERY_CAPACITY_KWH = 200

ASSUMED_CYCLE_LIFE = 4000

# Illustrative battery replacement cost.
# This is a simulation assumption, not a market quotation.
BATTERY_REPLACEMENT_COST_INR = 100000

# Estimated degradation cost per kWh of battery throughput.
DEGRADATION_COST_PER_KWH = (
    BATTERY_REPLACEMENT_COST_INR
    / (2 * BATTERY_CAPACITY_KWH * ASSUMED_CYCLE_LIFE)
)

print("APEMA DEGRADATION SETTINGS")
print("--------------------------")
print("Battery capacity:", BATTERY_CAPACITY_KWH, "kWh")
print("Assumed cycle life:", ASSUMED_CYCLE_LIFE)
print(
    "Degradation cost per kWh throughput: ₹",
    round(DEGRADATION_COST_PER_KWH, 4)
)