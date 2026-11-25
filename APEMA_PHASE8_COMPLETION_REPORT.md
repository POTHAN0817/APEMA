# APEMA Phase 8 Completion Report: Rolling-Horizon Forecasting & Optimization Integration

**Project Title:** Dynamic Price-Aware Solar, Battery & Grid Energy Management with Battery Life Optimization  
**System Name:** APEMA (Adaptive Price-Aware Energy Management Algorithm)  
**Phase Completed:** Phase 8 – Rolling-Horizon Forecasting and Optimization Integration using Model Predictive Control (MPC)  
**Date:** November 2026  
**Status:** Successfully Implemented, Tested, Validated, and Documented (34/34 Tests Passing, Frontend Production Build Passing)

---

## 1. Executive Summary

Phase 8 elevates the APEMA system from a static open-loop 24-hour optimizer into an industrial-grade **closed-loop Model Predictive Control (MPC)** system. 

The controller dynamically forecasts building electrical load, solar generation, and electricity tariffs over a 24-hour receding horizon, re-solves the MILP optimization at each discrete hourly time step with physical battery state feedback, executes strictly the first-hour dispatch decision, and logs realized commercial building energy metrics.

All requirements of Phase 8 have been fulfilled:
- **`RollingHorizonController`** built in `simulation/rolling_horizon_controller.py`.
- **Dynamic initial SOC** supported in `optimization/apema_optimizer.py` with zero breaking changes to existing static workflows.
- **Microservice API** extended with `POST /rolling-optimize`, `GET /results/rolling/{mode}`, and `GET /results/comparison`.
- **Interactive UI Dashboard** enhanced with a dedicated Rolling-Horizon MPC control and visualization section in React 19.
- **34 unit and integration tests** built and passing under `tests/`.
- **Frontend production build** verified with Vite (`tsc -b && vite build` clean).

---

## 2. New Files Created

1. **`simulation/rolling_horizon_controller.py`**
   - Implements the complete `RollingHorizonController` class.
   - Manages simulation clock, sliding 24-hour forecast windows, physical `BatteryModel` transitions, `BatteryDegradationModel` accounting, first-hour action execution, and CSV result exports.
2. **`simulation/compare_mpc_vs_static.py`**
   - Automated benchmark runner that evaluates all 5 MPC modes, static 24-hour APEMA optimization, and 3 heuristic baselines (*Solar First*, *Price Only*, *Degradation Aware*) over an identical 24-hour historical window.
   - Generates summary CSV and comparative Matplotlib plots.
3. **`tests/test_rolling_horizon.py`**
   - 17 unit and integration tests covering controller initialization, forecast window extraction, sliding window advancement, dynamic initial SOC feedback, first-action execution, physical state updates, power balance, constraint limits, boundary handling, and all 5 APEMA operating modes.
4. **`tests/test_battery_and_degradation.py`**
   - 5 tests validating battery physical state transitions, Coulombic charge/discharge efficiencies, SOC limits, and EFC degradation calculations.
5. **`tests/test_optimizer.py`**
   - 3 tests validating MILP solver power balance, mutual exclusion of charging and discharging, and dynamic initial SOC overrides.
6. **`tests/test_api.py`**
   - 8 tests verifying FastAPI endpoints (`GET /`, `GET /modes`, `GET /optimize/{mode}`, `GET /results/{mode}`, `POST /rolling-optimize`, `GET /results/rolling/{mode}`, `GET /results/comparison`, and error handling).
7. **`frontend/src/RollingHorizonMPC.tsx`**
   - Interactive React component featuring mode selection, duration slider, initial SOC control, progress indicators, KPI metric cards, comparative benchmark table, and 4 Plotly charts.
8. **`docs/ROLLING_HORIZON_MPC.md`**
   - In-depth engineering documentation detailing the mathematical formulation, forecast window mechanism, state feedback loop, API contracts, and performance analysis.
9. **`APEMA_PHASE8_COMPLETION_REPORT.md`**
   - Final completion report saved in project root.

---

## 3. Existing Files Modified

1. **`optimization/apema_optimizer.py`**
   - Modified `__init__` and `optimize()` to support dynamic `initial_soc` overrides and flexible terminal SOC targets without artificially constraining mid-day charged states.
   - Added numerical tolerance clipping ($10^{-5}$) to prevent spurious floating-point boundary errors.
2. **`backend/main.py`**
   - Added Pydantic request schema `RollingOptimizationRequest`.
   - Added `POST /rolling-optimize` to run the MPC controller and return execution summaries.
   - Added `GET /results/rolling/{mode}` to stream rolling execution CSV files.
   - Added `GET /results/comparison` to serve the benchmark comparison table.
3. **`frontend/src/App.tsx`**
   - Imported and embedded `RollingHorizonMPC.tsx` seamlessly into the dashboard layout.
   - Added sidebar navigation link `#mpc-section`.
   - Kept all five existing analysis sections completely intact.
4. **`README.md`**
   - Updated system status checklist, added Phase 8 documentation section, and detailed new API and testing capabilities.

---

## 4. MPC Architecture & Data Flow

```text
At each hourly time step k (timestamp t_k):
1. State Feedback: Read physical battery SOC_phys[k] and energy E_batt_phys[k].
2. Demand Forecast: Random Forest recursively predicts 24 hours ahead using lag-1 demand from t_{k-1}.
3. Solar Forecast: 100 kW PV physical model computes 24-hour generation from diurnal irradiance profile.
4. Tariff Schedule: 24-hour time-of-use tariff rates mapped from TariffModel.
5. Optimization: APEMA MILP optimizer solves optimal 24-hour dispatch subject to E_batt[0] = E_batt_phys[k].
6. Action Extraction: Extract P_ch[0] and P_dis[0] (discarding steps 1..23).
7. Physical Execution: Apply P_ch[0] and P_dis[0] to BatteryModel:
     E_batt_phys[k+1] = E_batt_phys[k] + P_ch[0]*dt*eta_ch - P_dis[0]*dt/eta_dis.
8. Realized Energy Balance:
     P_grid_real[k] = max(0, P_demand_real[k] + P_ch[0] - P_dis[0] - P_solar_real[k]).
9. Clock Advancement: t_k <- t_k + 1 hour, advance simulation step k <- k + 1, repeat.
```

---

## 5. Mathematical Formulation & Assumptions

1. **Planning Horizon:** Receding horizon $H = 24$ hours; control interval $\Delta t = 1.0$ hour.
2. **State Equation in MILP:**
   $$E_{\text{batt}}[0] - \eta_{\text{ch}} \Delta t P_{\text{ch}}[0] + \frac{\Delta t}{\eta_{\text{dis}}} P_{\text{dis}}[0] = E_{\text{batt}}^{\text{phys}}[k]$$
   $$E_{\text{batt}}[t] - E_{\text{batt}}[t-1] - \eta_{\text{ch}} \Delta t P_{\text{ch}}[t] + \frac{\Delta t}{\eta_{\text{dis}}} P_{\text{dis}}[t] = 0 \quad (\forall t \ge 1)$$
3. **Physical System Parameters:**
   - Battery Capacity: $200\text{ kWh}$.
   - Converter Limits: $P_{\text{ch}}^{\max} = P_{\text{dis}}^{\max} = 50\text{ kW}$ ($0.25\text{ C}$).
   - Operating Limits: $\text{SOC}_{\min} = \max(20\%, \text{reserve\_soc})$, $\text{SOC}_{\max} = 90\%$.
   - Efficiencies: $\eta_{\text{ch}} = \eta_{\text{dis}} = 0.95$ (Round-trip efficiency $\eta_{\text{RTE}} = 90.25\%$).
   - Replacement Cost: ₹100,000 for 4,000 cycles $\implies c_{\text{deg}} = ₹0.0625\text{/kWh throughput}$.

---

## 6. Execution & Test Results

### 6.1 Automated Pytest Test Suite
Executing `pytest -v tests/`:
```text
============================= test session starts =============================
platform win32 -- Python 3.12.6, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\duddu\Documents\APEMA project
collected 34 items

tests/test_api.py::test_api_root PASSED                                  [  2%]
tests/test_api.py::test_api_modes PASSED                                 [  5%]
tests/test_api.py::test_static_optimize_endpoint PASSED                  [  8%]
tests/test_api.py::test_static_results_endpoint PASSED                   [ 11%]
tests/test_api.py::test_rolling_optimize_endpoint PASSED                 [ 14%]
tests/test_api.py::test_rolling_results_endpoint PASSED                  [ 17%]
tests/test_api.py::test_comparison_endpoint PASSED                       [ 20%]
tests/test_api.py::test_invalid_modes_raise_http_exception PASSED        [ 23%]
tests/test_battery_and_degradation.py::test_battery_initial_state PASSED [ 26%]
tests/test_battery_and_degradation.py::test_battery_charge_efficiency PASSED [ 29%]
tests/test_battery_and_degradation.py::test_battery_discharge_efficiency PASSED [ 32%]
tests/test_battery_and_degradation.py::test_battery_capacity_caps PASSED [ 35%]
tests/test_battery_and_degradation.py::test_degradation_efc_calculation PASSED [ 38%]
tests/test_optimizer.py::test_optimizer_dynamic_initial_soc PASSED       [ 41%]
tests/test_optimizer.py::test_optimizer_power_balance PASSED             [ 44%]
tests/test_optimizer.py::test_optimizer_no_simultaneous_operation PASSED [ 47%]
tests/test_rolling_horizon.py::test_controller_initialization PASSED     [ 50%]
tests/test_rolling_horizon.py::test_invalid_mode_initialization PASSED   [ 52%]
tests/test_rolling_horizon.py::test_forecast_window_generation PASSED    [ 55%]
tests/test_rolling_horizon.py::test_forecast_window_advancement PASSED   [ 58%]
tests/test_rolling_horizon.py::test_dynamic_initial_soc_passed_to_optimizer PASSED [ 61%]
tests/test_rolling_horizon.py::test_only_first_control_action_executed PASSED [ 64%]
tests/test_rolling_horizon.py::test_battery_soc_updates_correctly PASSED [ 67%]
tests/test_rolling_horizon.py::test_soc_remains_within_configured_limits PASSED [ 70%]
tests/test_rolling_horizon.py::test_battery_power_limits_and_no_simultaneous_operation PASSED [ 73%]
tests/test_rolling_horizon.py::test_power_balance_for_executed_hours PASSED [ 76%]
tests/test_rolling_horizon.py::test_optimization_failure_handling PASSED [ 79%]
tests/test_rolling_horizon.py::test_boundary_handling_exceeding_dataset PASSED [ 82%]
tests/test_rolling_horizon.py::test_results_csv_generation PASSED        [ 85%]
tests/test_rolling_horizon.py::test_all_five_apema_modes[cost_saving] PASSED [ 88%]
tests/test_rolling_horizon.py::test_all_five_apema_modes[battery_life] PASSED [ 91%]
tests/test_rolling_horizon.py::test_all_five_apema_modes[solar_priority] PASSED [ 94%]
tests/test_rolling_horizon.py::test_all_five_apema_modes[backup_priority] PASSED [ 97%]
tests/test_rolling_horizon.py::test_all_five_apema_modes[balanced] PASSED [100%]

======================== 34 passed in 70.20s (0:01:10) ========================
```

### 6.2 Frontend Production Build
Executing `cd frontend && npm run build`:
```text
vite v8.3.7 building client environment for production...
transforming...
✓ 29 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                     0.45 kB │ gzip:     0.29 kB
dist/assets/index-BApuSelI.css     20.19 kB │ gzip:     4.78 kB
dist/assets/index-BXCuKC7E.js   4,975.84 kB │ gzip: 1,509.94 kB
✓ built in 3.12s
```
**Zero TypeScript errors, zero CSS errors.**

---

## 7. Results Files Locations

| File Path | Description |
|---|---|
| `results/rolling_horizon_results.csv` | Canonical rolling-horizon results CSV |
| `results/rolling_horizon_balanced_results.csv` | Mode-specific results for Balanced mode |
| `results/rolling_horizon_cost_saving_results.csv` | Mode-specific results for Cost Saving mode |
| `results/rolling_horizon_battery_life_results.csv` | Mode-specific results for Battery Life mode |
| `results/rolling_horizon_solar_priority_results.csv` | Mode-specific results for Solar Priority mode |
| `results/rolling_horizon_backup_priority_results.csv` | Mode-specific results for Backup Priority mode |
| `results/mpc_vs_static_comparison.csv` | Multi-strategy comparative benchmark table |
| `results/plots/mpc_vs_static_comparison.png` | 4-panel comparative benchmark visualization |

---

## 8. Quantitative Performance Comparison

Benchmarked on an identical 24-hour out-of-sample commercial office test day (`2017-09-01 00:00:00`):

| Strategy / Mode | Type | Grid Cost (₹) | Battery Throughput (kWh) | Degradation Cost (₹) | Final SOC (%) | Runtime (s) |
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

### Core Findings:
- **Cost Minimization:** `MPC (Cost Saving)` delivers the lowest realized cost (**₹131,162.54**), beating static cost saving by ₹65.78 and rule-based baselines by up to ₹128.15.
- **Physical Feasibility:** Power balance error remained strictly within $<10^{-4}\text{ kW}$ across all 24 executed steps.
- **Battery Health:** Operating bounds ($20\% \le \text{SOC} \le 90\%$) and zero simultaneous charging/discharging constraints were strictly maintained across all modes.

---

## 9. Remaining Technical Limitations

1. **XGBoost Load Forecasting:**
   - The current forecaster uses Scikit-learn `RandomForestRegressor`. Implementing XGBoost remains an outstanding milestone.
2. **Synthetic Solar Model:**
   - Solar PV generation uses a diurnal theoretical irradiance bell curve rather than real satellite or meteorological solar irradiance forecasts.
3. **Illustrative Electricity Tariff:**
   - The tariff model reflects a stepped Time-of-Use structure (₹4.00 to ₹8.00/kWh). Real commercial HT tariffs include kVA maximum demand charges and time-of-day surcharge slabs.

---

## 10. Conclusion

Phase 8 is fully completed, rigorously validated, and integrated into the APEMA system. All source code is committed locally, no external push was performed, and the system is ready for subsequent phases.

