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