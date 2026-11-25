import pytest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from battery.battery_model import BatteryModel
from battery.degradation_model import BatteryDegradationModel


def test_battery_initial_state():
    batt = BatteryModel(
        capacity_kwh=200,
        initial_soc=0.50,
        min_soc=0.20,
        max_soc=0.90
    )
    assert batt.capacity_kwh == 200
    assert batt.soc == 0.50
    assert batt.energy_kwh == 100.0


def test_battery_charge_efficiency():
    batt = BatteryModel(
        capacity_kwh=200,
        initial_soc=0.50,
        charge_efficiency=0.95
    )
    stored = batt.charge(power_kw=40, duration_hours=1)
    # Stored = 40 * 1 * 0.95 = 38.0 kWh
    assert stored == pytest.approx(38.0)
    assert batt.energy_kwh == pytest.approx(138.0)
    assert batt.soc == pytest.approx(138.0 / 200.0)


def test_battery_discharge_efficiency():
    batt = BatteryModel(
        capacity_kwh=200,
        initial_soc=0.80,
        discharge_efficiency=0.95
    )
    delivered = batt.discharge(power_kw=38, duration_hours=1)
    # Delivered = 38 kW * 1h = 38 kWh
    # Battery internal energy used = 38 / 0.95 = 40 kWh
    assert delivered == pytest.approx(38.0)
    assert batt.energy_kwh == pytest.approx(160.0 - 40.0)
    assert batt.soc == pytest.approx(120.0 / 200.0)


def test_battery_capacity_caps():
    batt = BatteryModel(
        capacity_kwh=200,
        initial_soc=0.85,
        max_soc=0.90,
        max_charge_kw=50
    )
    # Headroom to 90% is 0.90 * 200 - 170 = 10 kWh
    # Charging at 50 kW * 0.95 = 47.5 kWh would exceed headroom
    stored = batt.charge(power_kw=50)
    assert stored == pytest.approx(10.0)
    assert batt.soc == pytest.approx(0.90)


def test_degradation_efc_calculation():
    deg = BatteryDegradationModel(
        battery_capacity_kwh=200,
        cycle_life=4000
    )
    # 400 kWh throughput equals 1 Equivalent Full Cycle (2 * 200 kWh)
    degradation_pct = deg.calculate_degradation(charge_energy=200, discharge_energy=200)
    assert deg.total_throughput_kwh == 400.0
    # 1 cycle / 4000 * 100% = 0.025%
    assert degradation_pct == pytest.approx((1.0 / 4000) * 100)

