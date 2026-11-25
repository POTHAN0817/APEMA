import pytest
from fastapi import HTTPException
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.main import (
    home,
    get_modes,
    run_optimization,
    get_optimization_results,
    run_rolling_optimization,
    get_rolling_results,
    get_comparison_results,
    RollingOptimizationRequest
)


def test_api_root():
    """Test GET / health check endpoint function."""
    res = home()
    assert res["status"] == "running"
    assert "message" in res


def test_api_modes():
    """Test GET /modes returns all 5 operating modes."""
    res = get_modes()
    assert "available_modes" in res
    assert "balanced" in res["available_modes"]
    assert len(res["available_modes"]) == 5


def test_static_optimize_endpoint():
    """Test existing GET /optimize/{mode} endpoint function."""
    res = run_optimization("balanced")
    assert res["mode"] == "balanced"
    assert "total_grid_cost_inr" in res
    assert "battery_throughput_kwh" in res
    assert res["battery_throughput_kwh"] > 0


def test_static_results_endpoint():
    """Test existing GET /results/{mode} endpoint function."""
    res = get_optimization_results("balanced")
    assert Path(res.path).exists()
    assert res.media_type == "text/csv"


def test_rolling_optimize_endpoint():
    """Test new POST /rolling-optimize endpoint function."""
    req = RollingOptimizationRequest(
        mode="balanced",
        initial_soc=0.50,
        simulation_duration=3,
        optimization_horizon=24
    )
    res = run_rolling_optimization(req)
    assert res["simulation_status"] == "completed"
    assert res["mode"] == "balanced"
    assert res["iterations_completed"] == 3
    assert "total_grid_cost" in res
    assert "battery_throughput_kwh" in res
    assert "estimated_degradation_cost" in res
    assert "final_soc" in res


def test_rolling_results_endpoint():
    """Test GET /results/rolling/{mode} endpoint function."""
    res = get_rolling_results("balanced")
    assert Path(res.path).exists()
    assert res.media_type == "text/csv"


def test_comparison_endpoint():
    """Test GET /results/comparison endpoint function."""
    res = get_comparison_results()
    assert Path(res.path).exists()
    assert res.media_type == "text/csv"


def test_invalid_modes_raise_http_exception():
    """Test invalid modes raise HTTPException with status 400 or 404."""
    with pytest.raises(HTTPException) as exc1:
        run_optimization("nonexistent")
    assert exc1.value.status_code == 400

    with pytest.raises(HTTPException) as exc2:
        get_optimization_results("nonexistent")
    assert exc2.value.status_code == 404

    with pytest.raises(HTTPException) as exc3:
        req = RollingOptimizationRequest(mode="nonexistent")
        run_rolling_optimization(req)
    assert exc3.value.status_code == 400
