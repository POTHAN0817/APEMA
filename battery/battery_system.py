from battery_model import BatteryModel
from degradation_model import BatteryDegradationModel


class BatterySystem:

    def __init__(self):

        self.battery = BatteryModel()

        self.degradation = BatteryDegradationModel(
            battery_capacity_kwh=200,
            cycle_life=4000
        )

    def charge_battery(self, power_kw, duration_hours=1):

        previous_energy = self.battery.energy_kwh

        stored_energy = self.battery.charge(
            power_kw,
            duration_hours
        )

        actual_energy_change = (
            self.battery.energy_kwh - previous_energy
        )

        self.degradation.calculate_degradation(
            charge_energy=actual_energy_change,
            discharge_energy=0
        )

        return stored_energy

    def discharge_battery(self, power_kw, duration_hours=1):

        previous_energy = self.battery.energy_kwh

        delivered_energy = self.battery.discharge(
            power_kw,
            duration_hours
        )

        actual_energy_change = (
            previous_energy - self.battery.energy_kwh
        )

        self.degradation.calculate_degradation(
            charge_energy=0,
            discharge_energy=actual_energy_change
        )

        return delivered_energy

    def display_system_status(self):

        print("\nAPEMA BATTERY SYSTEM STATUS")
        print("===========================")

        self.battery.display_status()
        self.degradation.display_status()


if __name__ == "__main__":

    system = BatterySystem()

    print("\nINITIAL STATUS")
    system.display_system_status()

    print("\nCHARGING BATTERY")
    system.charge_battery(40)

    print("\nDISCHARGING BATTERY")
    system.discharge_battery(30)

    print("\nFINAL STATUS")
    system.display_system_status()