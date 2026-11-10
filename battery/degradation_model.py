class BatteryDegradationModel:

    def __init__(
        self,
        battery_capacity_kwh=200,
        cycle_life=4000
    ):
        self.battery_capacity_kwh = battery_capacity_kwh
        self.cycle_life = cycle_life
        self.total_throughput_kwh = 0

    def calculate_degradation(self, charge_energy, discharge_energy):

        throughput = charge_energy + discharge_energy

        self.total_throughput_kwh += throughput

        # One equivalent full cycle represents
        # twice the battery capacity in throughput.
        equivalent_cycles = (
            self.total_throughput_kwh
            / (2 * self.battery_capacity_kwh)
        )

        degradation_percentage = (
            equivalent_cycles / self.cycle_life
        ) * 100

        return degradation_percentage

    def display_status(self):

        degradation = (
            self.total_throughput_kwh
            / (2 * self.battery_capacity_kwh * self.cycle_life)
        ) * 100

        print("\nBATTERY DEGRADATION STATUS")
        print("==========================")
        print("Total throughput:", round(self.total_throughput_kwh, 2), "kWh")
        print("Estimated degradation:", round(degradation, 6), "%")


if __name__ == "__main__":

    battery_degradation = BatteryDegradationModel()

    print("\nSIMULATING BATTERY USAGE")

    degradation = battery_degradation.calculate_degradation(
        charge_energy=40,
        discharge_energy=30
    )

    print("Estimated degradation:", round(degradation, 6), "%")

    battery_degradation.display_status()