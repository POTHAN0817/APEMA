from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

import pandas as pd
import sys
from pathlib import Path


# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Add project root to Python path
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# Import optimizer using package paths
from optimization.apema_optimizer import APEMAOptimizer
from optimization.apema_modes import APEMA_MODES
from simulation.rolling_horizon_controller import RollingHorizonController
from pydantic import BaseModel, Field
from typing import Optional


class RollingOptimizationRequest(BaseModel):
    mode: str = Field(default="balanced", description="APEMA operating mode")
    initial_soc: float = Field(default=0.50, ge=0.20, le=0.90, description="Initial battery SOC (0.20 to 0.90)")
    simulation_duration: int = Field(default=24, ge=1, le=168, description="Simulation duration in hours")
    optimization_horizon: int = Field(default=24, ge=1, le=48, description="Planning horizon in hours")
    start_time: Optional[str] = Field(default=None, description="Start timestamp string")


# Initialize FastAPI
app = FastAPI(
    title="APEMA Energy Management API",
    description="Adaptive Price-Aware Energy Management Algorithm",
    version="1.0.0"
)


# Frontend connection settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Optimizer input dataset
INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "apema_optimizer_input.csv"
)


@app.get("/")
def home():
    return {
        "message": "Welcome to APEMA Energy Management API",
        "status": "running"
    }


@app.get("/modes")
def get_modes():
    return {
        "available_modes": APEMA_MODES
    }


@app.get("/optimize/{mode}")
def run_optimization(mode: str):

    try:
        if mode not in APEMA_MODES:
            raise HTTPException(
                status_code=400,
                detail="Invalid APEMA operating mode."
            )

        if not INPUT_FILE.exists():
            raise HTTPException(
                status_code=404,
                detail="Optimizer input dataset not found."
            )

        data = pd.read_csv(INPUT_FILE)

        optimizer = APEMAOptimizer(mode=mode)

        results, objective_value = optimizer.optimize(data)

        output_file = (
            PROJECT_ROOT
            / "results"
            / f"api_{mode}_results.csv"
        )

        results.to_csv(output_file, index=False)

        return {
            "mode": mode,
            "objective_value": float(objective_value),
            "total_grid_cost_inr": float(
                results["grid_cost_inr"].sum()
            ),
            "battery_throughput_kwh": float(
                results["battery_throughput_kwh"].sum()
            ),
            "final_soc_percent": float(
                results["battery_soc"].iloc[-1] * 100
            ),
            "results_file": str(output_file)
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


@app.get("/results/{mode}")
def get_optimization_results(mode: str):
    if mode not in APEMA_MODES:
        raise HTTPException(
            status_code=404,
            detail="Invalid APEMA mode"
        )

    results_file = (
        PROJECT_ROOT
        / "results"
        / f"api_{mode}_results.csv"
    )

    if not results_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Optimization results not found. Run optimization first."
        )

    return FileResponse(
        path=results_file,
        media_type="text/csv",
        filename=f"apema_{mode}_results.csv"
    )


@app.post("/rolling-optimize")
def run_rolling_optimization(request: RollingOptimizationRequest):
    try:
        if request.mode not in APEMA_MODES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid APEMA operating mode: {request.mode}."
            )

        controller = RollingHorizonController(
            mode=request.mode,
            initial_soc=request.initial_soc,
            simulation_duration=request.simulation_duration,
            planning_horizon=request.optimization_horizon,
            start_time=request.start_time
        )

        results = controller.run()

        output_file = (
            PROJECT_ROOT
            / "results"
            / f"api_rolling_{request.mode}_results.csv"
        )
        controller.save_results(output_path=str(output_file))

        total_grid_cost = float(results["grid_cost_inr"].sum())
        total_throughput = float(results["battery_throughput_kwh"].sum())
        total_degradation_cost = float(results["degradation_cost_inr"].sum())
        final_soc = float(results["battery_soc"].iloc[-1] * 100)

        return {
            "simulation_status": "completed",
            "mode": request.mode,
            "total_grid_cost": total_grid_cost,
            "total_grid_cost_inr": total_grid_cost,
            "total_battery_throughput": total_throughput,
            "battery_throughput_kwh": total_throughput,
            "estimated_degradation_cost": total_degradation_cost,
            "degradation_cost_inr": total_degradation_cost,
            "final_soc": final_soc,
            "final_soc_percent": final_soc,
            "results_file": str(output_file),
            "number_of_iterations": len(results),
            "iterations_completed": len(results)
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


@app.get("/results/rolling/{mode}")
def get_rolling_results(mode: str):
    if mode not in APEMA_MODES:
        raise HTTPException(
            status_code=404,
            detail="Invalid APEMA mode."
        )

    results_file = (
        PROJECT_ROOT
        / "results"
        / f"api_rolling_{mode}_results.csv"
    )

    if not results_file.exists():
        fallback_file = (
            PROJECT_ROOT
            / "results"
            / f"rolling_horizon_{mode}_results.csv"
        )
        if fallback_file.exists():
            results_file = fallback_file
        else:
            raise HTTPException(
                status_code=404,
                detail="Rolling-horizon optimization results not found. Run rolling optimization first."
            )

    return FileResponse(
        path=results_file,
        media_type="text/csv",
        filename=f"apema_rolling_{mode}_results.csv"
    )


@app.get("/results/comparison")
def get_comparison_results():
    results_file = (
        PROJECT_ROOT
        / "results"
        / "mpc_vs_static_comparison.csv"
    )

    if not results_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Comparison benchmark results not found."
        )

    return FileResponse(
        path=results_file,
        media_type="text/csv",
        filename="mpc_vs_static_comparison.csv"
    )
