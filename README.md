# APEMA
### Adaptive Price-Aware Energy Management Algorithm

**Dynamic Price-Aware Solar, Battery & Grid Energy Management with Battery Life Optimization**

APEMA is an intelligent energy management system designed for commercial buildings. It optimizes the hourly operation of solar photovoltaic generation, battery energy storage and grid electricity imports while considering electricity tariffs, battery operating constraints and battery degradation.

The project combines forecasting, mathematical optimization, battery simulation and an interactive web dashboard.

---

## 1. Project Objectives

- Minimize electricity purchasing costs.
- Optimize solar energy utilization.
- Reduce unnecessary battery cycling.
- Account for battery degradation.
- Maintain battery State of Charge (SOC) within operating limits.
- Compare APEMA strategies against baseline energy management strategies.

## 2. APEMA Operating Modes

The system implements five operating modes:

| Mode | Objective |
|---|---|
| Cost Saving | Reduce electricity costs |
| Battery Life | Minimize battery cycling and degradation |
| Solar Priority | Prioritize solar energy utilization |
| Backup Priority | Maintain additional battery reserve |
| Balanced | Balance cost, solar utilization and battery life |

## 3. System Architecture

The APEMA workflow follows:

1. Input Data
2. Demand and Solar Forecasting
3. Battery Modelling
4. APEMA Optimization
5. Energy Management Decision
6. Performance Evaluation
7. Hourly Update

## 4. Technology Stack

| Component | Technology |
|---|---|
| Development Environment | Google Antigravity |
| Programming Language | Python |
| Numerical Computing | NumPy |
| Data Processing | Pandas |
| Forecasting | Scikit-learn |
| Optimization | SciPy MILP |
| Battery Simulation | Custom Python |
| Degradation Modelling | Mathematical Proxy |
| Backend | FastAPI |
| Frontend | React.js, TypeScript |
| Visualization | Plotly.js |
| Styling | Tailwind CSS |
| Data Storage | CSV |
| Version Control | Git and GitHub |
| Testing | Pytest |

## 5. Project Structure

```text
APEMA project/
│
├── backend/
│   ├── main.py
│   └── __init__.py
│
├── battery/
│   ├── battery_model.py
│   ├── battery_system.py
│   └── degradation_model.py
│
├── data/
│   ├── analysis/
│   ├── preprocessing/
│   └── processed/
│
├── evaluation/
│   └── performance_analysis.py
│
├── forecasting/
│   ├── demand_forecast.py
│   └── predict_demand.py
│
├── optimization/
│   ├── apema_optimizer.py
│   ├── apema_modes.py
│   ├── baseline_strategies.py
│   └── ...
│
├── results/
│   └── plots/
│
├── simulation/
│
├── solar/
│
├── tariff/
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── EnergyCharts.tsx
│   │   ├── BatterySOC.tsx
│   │   ├── SolarIndicator.tsx
│   │   └── GridMonitoring.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── main.py
├── README.md
└── .gitignore
```

## 6. Dataset

The project uses the Building Data Genome Project 2 (BDG2), a benchmark dataset containing building energy consumption data.

Selected building:
- Building: Hog_office_Byron
- Building type: Office
- Location group: Hog
- Floor area: 80,038.2 m²
- Data frequency: Hourly
- Observation period: 2016–2017

The original raw dataset is not included in this repository. Processed project data and analysis outputs are included.

Dataset source: https://github.com/buds-lab/building-data-genome-project-2

## 7. Simulation Configuration

The current energy management simulation uses:

| Parameter | Value |
|---|---:|
| Solar PV capacity | 100 kW |
| Battery capacity | 200 kWh |
| Maximum charging power | 50 kW |
| Maximum discharging power | 50 kW |
| Minimum SOC | 20% |
| Maximum SOC | 90% |
| Initial SOC | 50% |
| Charging efficiency | 95% |
| Discharging efficiency | 95% |
| Optimization horizon | 24 hours |
| Time interval | 1 hour |

**Note:** The solar generation profile and electricity tariff currently use illustrative simulated inputs. They should not be interpreted as measured solar generation or official electricity tariffs.

The battery degradation calculation is a mathematical throughput-based proxy, not a direct measurement of battery State of Health.

## 8. Installation and Execution

### Prerequisites

- Python 3.12
- Node.js and npm
- Git

### Step 1: Clone the repository

```bash
git clone https://github.com/POTHAN0817/APEMA.git
cd APEMA
```

### Step 2: Create a Python virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install Python dependencies

```powershell
pip install numpy pandas scipy scikit-learn fastapi uvicorn joblib matplotlib pytest
```

### Step 4: Start the backend

From the project root:

```powershell
python -m uvicorn backend.main:app --reload
```

Backend address:

http://127.0.0.1:8000

API documentation:

http://127.0.0.1:8000/docs

### Step 5: Install frontend dependencies

Open another terminal:

```powershell
cd frontend
npm install
```

### Step 6: Start the frontend

```powershell
npm run dev
```

Open the local Vite address displayed in the terminal, normally:

http://localhost:5173

## 9. Dashboard Features

The APEMA web dashboard provides:

- Five selectable energy management modes.
- Optimization execution through FastAPI.
- Grid electricity cost monitoring.
- Battery State of Charge visualization.
- Solar generation and utilization monitoring.
- Grid import and dependency monitoring.
- Hourly energy performance charts.
- Optimization result retrieval through CSV files.

## 10. Performance Evaluation

APEMA is evaluated against baseline energy management strategies.

The comparison considers:

- Electricity cost.
- Grid energy imports.
- Solar energy utilization.
- Battery throughput.
- Estimated battery degradation.
- Battery SOC.
- Optimization performance.

The objective is to evaluate the trade-offs between electricity cost reduction, solar utilization and battery life.

## 11. Current Development Status

- [x] Building energy dataset preprocessing
- [x] Demand forecasting pipeline
- [x] Solar generation simulation
- [x] Battery modelling
- [x] Battery degradation proxy
- [x] Hourly tariff model
- [x] MILP-based APEMA optimization
- [x] Five energy management modes
- [x] Baseline strategy comparison
- [x] FastAPI backend
- [x] React and TypeScript dashboard
- [x] Battery SOC visualization
- [x] Solar energy monitoring
- [x] Grid energy monitoring
- [x] Rolling-Horizon Model Predictive Control (MPC) integration (Phase 8)
- [x] Automated pytest testing suite (34 unit & integration tests)
- [x] Advanced battery performance analytics
- [ ] Further model and forecast improvements (e.g. XGBoost)

## 12. Model Predictive Control (Phase 8)

APEMA implements closed-loop Model Predictive Control (MPC) in `simulation/rolling_horizon_controller.py`:
- **Rolling Forecast Window:** Dynamically updates 24-hour demand forecasts using lag-1 load feedback, alongside diurnal PV and tariff schedules.
- **Physical Battery State Feedback:** Re-solves the MILP optimizer hourly, executes only the first-hour action ($P_{\text{ch}}[0], P_{\text{dis}}[0]$), updates physical battery SOC with real converter efficiencies, and logs realized building energy balance.
- **REST API Endpoints:** `POST /rolling-optimize`, `GET /results/rolling/{mode}`, and `GET /results/comparison`.
- **Frontend Integration:** Dedicated interactive MPC section with configuration controls, KPI cards, and comparative Plotly charts.
- **Full Documentation:** See [docs/ROLLING_HORIZON_MPC.md](file:///c:/Users/duddu/Documents/APEMA%20project/docs/ROLLING_HORIZON_MPC.md).

## 12. Important Limitations

- The solar generation profile is currently simulated.
- The electricity tariff is illustrative, not an official utility tariff.
- The current demand forecasting implementation uses RandomForestRegressor; the planned XGBoost implementation remains future work.
- The degradation model estimates degradation using battery throughput and assumed cycle life.
- Results represent simulation outputs and should not be interpreted as live building energy measurements.

---

**Project:** APEMA – Adaptive Price-Aware Energy Management Algorithm

**Focus:** Commercial Building Energy Management, Solar PV, Battery Storage, Grid Optimization and Battery Life Optimization.