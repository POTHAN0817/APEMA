class BatteryModel:

    def __init__(
        self,
        capacity_kwh=200,
        max_charge_kw=50,
        max_discharge_kw=50,
        min_soc=0.20,
        max_soc=0.90,
        initial_soc=0.50,
        charge_efficiency=0.95,
        discharge_efficiency=0.95
    ):

        self.capacity_kwh = capacity_kwh
        self.max_charge_kw = max_charge_kw
        self.max_discharge_kw = max_discharge_kw
        self.min_soc = min_soc
        self.max_soc = max_soc
        self.soc = initial_soc
        self.charge_efficiency = charge_efficiency
        self.discharge_efficiency = discharge_efficiency
        self.energy_kwh = self.soc * self.capacity_kwh

    def charge(self, power_kw, duration_hours=1):

        if power_kw < 0 or duration_hours < 0:
            raise ValueError("Power and duration cannot be negative.")

        power_kw = min(power_kw, self.max_charge_kw)

        available_capacity = (
            self.max_soc * self.capacity_kwh - self.energy_kwh
        )

        accepted_energy = min(
            power_kw * duration_hours * self.charge_efficiency,
            available_capacity
        )

        self.energy_kwh += accepted_energy
        self.soc = self.energy_kwh / self.capacity_kwh

        return accepted_energy

    def discharge(self, power_kw, duration_hours=1):

        if power_kw < 0 or duration_hours < 0:
            raise ValueError("Power and duration cannot be negative.")

        power_kw = min(power_kw, self.max_discharge_kw)

        available_energy = (
            self.energy_kwh - self.min_soc * self.capacity_kwh
        )

        delivered_energy = min(
            power_kw * duration_hours,
            available_energy * self.discharge_efficiency
        )

        battery_energy_used = delivered_energy / self.discharge_efficiency

        self.energy_kwh -= battery_energy_used
        self.soc = self.energy_kwh / self.capacity_kwh

        return delivered_energy

    def display_status(self):

        print("Battery SOC:", round(self.soc * 100, 2), "%")
        print("Stored energy:", round(self.energy_kwh, 2), "kWh")


if __name__ == "__main__":

    battery = BatteryModel()

    print("\nTEST 1: MAXIMUM CHARGING POWER")
    charged = battery.charge(80, duration_hours=1)
    print("Requested power: 80 kW")
    print("Maximum allowed power: 50 kW")
    print("Energy stored:", charged, "kWh")
    battery.display_status()

    print("\nTEST 2: MAXIMUM DISCHARGING POWER")

    battery = BatteryModel(initial_soc=0.90)

    discharged = battery.discharge(80, duration_hours=1)
    print("Requested power: 80 kW")
    print("Maximum allowed power: 50 kW")
    print("Energy delivered:", discharged, "kWh")
    battery.display_status()