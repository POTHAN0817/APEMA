import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from optimization.apema_optimizer import APEMAOptimizer
from optimization.apema_modes import APEMA_MODES


def test_optimizer_dynamic_initial_soc():
    """Verify optimizer runs with updated dynamic initial SOC."""
    data = pd.read_csv(PROJECT_ROOT / "data" / "processed" / "apema_optimizer_input.csv")

    optimizer = APEMAOptimizer(mode="balanced", initial_soc=0.50)
    res1, obj1 = optimizer.optimize(data, initial_soc=0.50)
    assert res1["battery_soc"].iloc[0] is not None

    # Re-run with initial_soc = 0.70
    res2, obj2 = optimizer.optimize(data, initial_soc=0.70)
    assert optimizer.initial_soc == pytest.approx(0.70)


def test_optimizer_power_balance():
    """Verify solver output satisfies power balance at all time intervals."""
    data = pd.read_csv(PROJECT_ROOT / "data" / "processed" / "apema_optimizer_input.csv")
    optimizer = APEMAOptimizer(mode="cost_saving")
    res, _ = optimizer.optimize(data)

    lhs = res["grid_import_kw"] + res["solar_used_kw"] + res["battery_discharge_kw"]
    rhs = res["demand_kw"] + res["battery_charge_kw"]
    diff = np.abs(lhs - rhs)
    assert (diff < 1e-4).all()


def test_optimizer_no_simultaneous_operation():
    """Verify mutual exclusion of charge and discharge."""
    data = pd.read_csv(PROJECT_ROOT / "data" / "processed" / "apema_optimizer_input.csv")
    optimizer = APEMAOptimizer(mode="balanced")
    res, _ = optimizer.optimize(data)

    simultaneous = (res["battery_charge_kw"] > 1e-4) & (res["battery_discharge_kw"] > 1e-4)
    assert not simultaneous.any()

