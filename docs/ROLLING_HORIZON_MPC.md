# APEMA – Phase 8: Rolling-Horizon Model Predictive Control (MPC) Integration

## 1. Overview

**Phase 8** integrates a **closed-loop Model Predictive Control (MPC)** framework into the APEMA (Adaptive Price-Aware Energy Management Algorithm) architecture. Previously, APEMA executed a single, open-loop, static 24-hour dispatch schedule. Under real-world operation, load forecast deviations, weather fluctuations, and battery model inaccuracies accumulate over time.

The Rolling-Horizon MPC architecture solves this by:
1. Generating a dynamic 24-hour forward forecast for building demand, solar generation, and time-of-use tariffs.
2. Solving the APEMA Mixed-Integer Linear Program (MILP) across the 24-hour planning horizon using the current battery state as initial condition.
3. Extracting and executing **only the first-hour control action** on the physical battery energy storage system.
4. Measuring realized power flows, updating the physical battery state of charge (SOC) with converter efficiency losses, and calculating empirical degradation.
5. Advancing the simulation clock by one hour, updating the lag demand state, sliding the 24-hour forecast window, and repeating the optimization with state feedback.

---

## 2. MPC System Architecture

```text
       +---------------------------------------------+
       |   Historical Demand Data (BDG2 Byron Load)  |
       +---------------------------------------------+
                              |
                              v
       +---------------------------------------------+
       |        Recursive 24-Hour Forecaster         |
       |  (Trained Random Forest with lag-1 update)  |
       +---------------------------------------------+
                              |
                              v
       +---------------------------------------------+
       |           24-Hour Forecast Window           |
       |  (Predicted Demand, Solar PV, TOU Tariff)   |
       +---------------------------------------------+
                              |
                              +<--------------------------+
                              |                           |
                              v                           |
       +---------------------------------------------+    |
       |             APEMA MILP Optimizer            |    |
       |       (SciPy HiGHS Solver, 5 Modes)         |    |
       +---------------------------------------------+    |
                              |                           |
                              v                           |
       +---------------------------------------------+    | (State
       |         Extract First-Hour Action           |    |  Feedback)
       |          (Charge/Discharge Power)           |    |
       +---------------------------------------------+    |
                              |                           |
                              v                           |
       +---------------------------------------------+    |
       |           Physical Battery Model            |    |
       |     (Coulombic efficiencies: 95%/95%)       |    |
       +---------------------------------------------+    |
                              |                           |
                              v                           |
       +---------------------------------------------+    |
       |        Update Battery Energy and SOC        |----+
       +---------------------------------------------+
                              |
                              v
       +---------------------------------------------+
       |      Advance Simulation Clock (dt = 1h)     |
       +---------------------------------------------+
                              |
                              v
       +---------------------------------------------+
       |       Log Realized Energy Balance & Cost    |
       +---------------------------------------------+
```

---

## 3. Mathematical Formulation & Assumptions

### 3.1 Receding Horizon Horizon Formulation
At each discrete simulation step $k$ with timestamp $t_k$:
- Planning horizon length: $H = 24$ hours.
- Control interval: $\Delta t = 1.0$ hour.
- Horizon indices: $t \in \{0, 1, \dots, H-1\}$ corresponding to future times $t_k, t_k + \Delta t, \dots, t_k + (H-1)\Delta t$.

### 3.2 Dynamic Initial State Constraint
The initial state of the battery for the optimization problem is constrained to match the physical state of the battery at step $k$:
$$E_{\text{batt}}[0] - \eta_{\text{ch}} \Delta t P_{\text{ch}}[0] + \frac{\Delta t}{\eta_{\text{dis}}} P_{\text{dis}}[0] = E_{\text{batt}}^{\text{phys}}[k]$$
where $E_{\text{batt}}^{\text{phys}}[k] = \text{SOC}^{\text{phys}}[k] \times C_{\text{batt}}$.

### 3.3 Terminal Constraint
For stability and energy reservation across receding horizons:
$$E_{\text{batt}}[H-1] \ge \text{SOC}_{\text{term}}^{\text{mode}} \times C_{\text{batt}}$$

### 3.4 First-Step Control Execution
Only the decision vector for interval $t=0$ is implemented on the physical asset:
$$P_{\text{ch}}^{\text{exec}}[k] = P_{\text{ch}}^{*}[0], \quad P_{\text{dis}}^{\text{exec}}[k] = P_{\text{dis}}^{*}[0]$$

### 3.5 Physical State Transition & Feedback
The actual battery energy state transitions physically:
$$E_{\text{batt}}^{\text{phys}}[k+1] = E_{\text{batt}}^{\text{phys}}[k] + P_{\text{ch}}^{\text{exec}}[k] \Delta t \eta_{\text{ch}} - \frac{P_{\text{dis}}^{\text{exec}}[k] \Delta t}{\eta_{\text{dis}}}$$
$$\text{SOC}^{\text{phys}}[k+1] = \frac{E_{\text{batt}}^{\text{phys}}[k+1]}{C_{\text{batt}}}$$
Subject to hard physical capacity bounds:
$$\text{SOC}_{\min}^{\text{mode}} \le \text{SOC}^{\text{phys}}[k+1] \le \text{SOC}_{\max}$$

### 3.6 Realized Power Balance
At time step $k$, with actual realized commercial building demand $P_{\text{demand}}^{\text{real}}[k]$ and actual solar generation $P_{\text{solar}}^{\text{real}}[k]$:
$$P_{\text{grid}}^{\text{real}}[k] = \max\left(0, \; P_{\text{demand}}^{\text{real}}[k] + P_{\text{ch}}^{\text{exec}}[k] - P_{\text{dis}}^{\text{exec}}[k] - P_{\text{solar}}^{\text{real}}[k]\right)$$
$$P_{\text{curt}}^{\text{real}}[k] = \max\left(0, \; P_{\text{solar}}^{\text{real}}[k] - (P_{\text{demand}}^{\text{real}}[k] - P_{\text{dis}}^{\text{exec}}[k] + P_{\text{ch}}^{\text{exec}}[k])\right)$$
$$P_{\text{solar\_used}}^{\text{real}}[k] = P_{\text{solar}}^{\text{real}}[k] - P_{\text{curt}}^{\text{real}}[k]$$
$$\text{Cost}_{\text{grid}}^{\text{real}}[k] = P_{\text{grid}}^{\text{real}}[k] \times c_{\text{tariff}}[k] \times \Delta t$$

---

## 4. Forecasting Window Mechanism

### 4.1 Recursive Demand Forecaster
- **Model:** Pretrained Scikit-learn `RandomForestRegressor` (`forecasting/models/demand_model.pkl`).
- **Features:** `[hour, day_of_week, month, previous_hour]`.
- **Closed-Loop Feedback:** At step $k$, `previous_hour` is initialized with the true observed demand from $k-1$: $P_{\text{demand}}^{\text{real}}[k-1]$.
- For subsequent horizon hours $\tau \in \{1, \dots, 23\}$, the forecaster uses its own previous predictions recursively.
- **Zero Future Data Leakage:** Realized future demands $P_{\text{demand}}^{\text{real}}[k \dots k+23]$ are never passed to the forecasting model or optimizer.

### 4.2 Diurnal Solar PV Generation
Calculated using the physical 100 kW model:
$$P_{\text{solar}}[\tau] = \min\left(100, 100 \times \frac{G[\tau.\text{hour}]}{1000} \times 0.80\right)$$

### 4.3 Time-of-Use Electricity Tariff
Retrieved from `TariffModel` based on hour of day ($₹4.00$ to $₹8.00\text{/kWh}$).

---

## 5. Benchmark Performance Comparison

Evaluation across an identical 24-hour test period (`2017-09-01 00:00:00`, commercial weekday load):

| Strategy / Mode | Strategy Type | Grid Cost (₹) | Battery Throughput (kWh) | Degradation Cost (₹) | Final SOC (%) | Runtime (s) |
|---|---|---:|---:|---:|---:|---:|
| **MPC (Cost Saving)** | Rolling Horizon | **₹131,162.54** | 267.21 | ₹8.35 | 43.8% | 22.95s |
| **MPC (Battery Life)** | Rolling Horizon | ₹131,618.54 | 210.21 | ₹131.38 | 73.8% | 21.63s |
| **MPC (Solar Priority)** | Rolling Horizon | ₹131,162.54 | 267.21 | ₹16.70 | 43.8% | 22.83s |
| **MPC (Backup Priority)**| Rolling Horizon | ₹131,618.54 | 210.21 | ₹26.28 | 73.8% | 32.86s |
| **MPC (Balanced)** | Rolling Horizon | ₹131,466.54 | 229.21 | ₹28.65 | 63.8% | 54.19s |
| **Static (Cost Saving)** | Static MILP | ₹131,228.32 | 280.37 | ₹8.76 | 50.0% | 0.05s |
| **Static (Balanced)** | Static MILP | ₹131,350.75 | 200.26 | ₹25.03 | 50.0% | 0.05s |
| **Baseline (Solar First)** | Heuristic | ₹131,290.69 | 57.00 | ₹3.56 | 20.0% | 0.03s |
| **Baseline (Price Only)** | Heuristic | ₹131,262.54 | 267.21 | ₹16.70 | 43.8% | 0.00s |
| **Baseline (Degradation Aware)**| Heuristic | ₹131,283.69 | 57.00 | ₹3.56 | 20.0% | 0.00s |

### Key Observations:
1. **Cost Improvement:** `MPC (Cost Saving)` achieved the lowest grid cost (**₹131,162.54**), saving ₹65.78 compared to static cost saving and ₹100.00 to ₹128.15 compared to rule-based baselines.
2. **Dynamic Reserve Adherence:** `MPC (Battery Life)` and `MPC (Backup Priority)` maintained higher terminal energy states (73.8% SOC) and respected the strict 50% minimum SOC reserve limit throughout the 24 hours.
3. **Runtime Trade-Off:** Rolling-Horizon MPC requires solving 24 sequential MILP optimization problems with Random Forest inference, taking ~22–32 seconds per 24-hour simulation, compared to 0.05s for a single static run.

---

## 6. API Integration

### Endpoint: `POST /rolling-optimize`
- **Request Body:**
  ```json
  {
    "mode": "balanced",
    "initial_soc": 0.50,
    "simulation_duration": 24,
    "optimization_horizon": 24,
    "start_time": null
  }
  ```
- **Response Body:**
  ```json
  {
    "simulation_status": "completed",
    "mode": "balanced",
    "total_grid_cost": 131466.54,
    "total_grid_cost_inr": 131466.54,
    "total_battery_throughput": 229.21,
    "battery_throughput_kwh": 229.21,
    "estimated_degradation_cost": 28.65,
    "degradation_cost_inr": 28.65,
    "final_soc": 63.75,
    "final_soc_percent": 63.75,
    "results_file": ".../results/api_rolling_balanced_results.csv",
    "number_of_iterations": 24,
    "iterations_completed": 24
  }
  ```

### Endpoint: `GET /results/rolling/{mode}`
Streams the generated 24-step rolling-horizon hourly execution CSV.

### Endpoint: `GET /results/comparison`
Streams the multi-strategy benchmark table (`mpc_vs_static_comparison.csv`).

---

## 7. Automated Test Suite

A comprehensive `pytest` test suite is implemented in `tests/`:
- **`tests/test_rolling_horizon.py`**: 17 tests verifying initialization, window generation, temporal advancement, dynamic SOC feedback, physical battery updates, limits enforcement, power balance, error handling, boundary conditions, and all 5 operating modes.
- **`tests/test_api.py`**: 8 tests verifying all FastAPI REST endpoints.
- **`tests/test_battery_and_degradation.py`**: 5 tests verifying physical battery efficiencies, state transitions, and EFC degradation calculation.
- **`tests/test_optimizer.py`**: 3 tests verifying dynamic initial SOC and MILP constraint satisfaction.

**Result: 34 / 34 tests passing.**

