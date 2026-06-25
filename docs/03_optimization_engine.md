# 03. Optimization Engine

The core intelligence of the application resides in `backend/services/optimizer.py`. We use **Linear Programming (LP)** to solve the charging scheduling problem.

---

## LP Formulation with Vehicle-to-Grid (V2G)

In Phase 4, the optimization engine was extended from simple charge-scheduling to bidirectional scheduling (V2G), enabling the vehicle to discharge energy back to the grid during peak pricing hours while ensuring the battery is charged by departure time.

### 1. Decision Variables
For each hourly slot $t$ in the charging window $T$:
- $c_t$: Energy charged (in kWh) during time slot $t$. Bounded: $0 \leq c_t \leq \text{MaxChargeRate}$.
- $d_t$: Energy discharged (in kWh) during time slot $t$. Bounded: $0 \leq d_t \leq \text{MaxDischargeRate}$ (only defined when V2G is enabled).

### 2. Objective Function
The objective is to minimize net electricity cost (charging costs minus grid sell-back revenue). To protect the battery, a small penalty is added to charging during high-temperature hours:

$$\text{Minimize} \sum_{t \in T} \left( (\text{Price}_t + \text{Penalty}_t) \times c_t \right) - \sum_{t \in T} \left( \text{Price}_t \times \gamma \times d_t \right)$$

Where:
- $\text{Price}_t$: The dynamic TOU electricity price for slot $t$.
- $\text{Penalty}_t$: A temperature-dependent scaling factor to deter charging in extreme heat.
- $\gamma$: The V2G buy-back rate multiplier (default: $0.85$, meaning the utility pays 85% of the spot price).

### 3. Constraints
The solver must respect physical limits and the user's constraints:

- **Net Energy per Slot**: The net change in battery energy during slot $t$ accounts for round-trip efficiency ($\eta$, default $90\%$):
  $$\Delta E_t = (c_t \times \eta) - \left( \frac{d_t}{\eta} \right)$$
- **Cumulative Energy Constraint**: The total energy in the battery at any slot $t$ cannot exceed usable capacity:
  $$0 \leq E_{\text{current}} + \sum_{i=1}^{t} \Delta E_i \leq \text{UsableCapacity}$$
- **V2G Safety Floor (SoC Floor)**: To prevent draining the vehicle's battery entirely, the state of charge cannot drop below a configurable safety floor (default: $20\%$ SoC) during V2G discharging:
  $$E_{\text{current}} + \sum_{i=1}^{t} \Delta E_i \geq \text{UsableCapacity} \times \text{MinSoCFloor}$$
- **Departure Target**: The battery must meet or exceed the target SoC at the departure hour:
  $$E_{\text{current}} + \sum_{t \in T} \Delta E_t \geq \text{UsableCapacity} \times \text{TargetSoC}$$

---

## Solver Technology: PuLP and CBC

- **PuLP**: A python library to model LP problems using native Python expressions.
- **CBC (COIN-OR Branch and Cut)**: A high-performance, open-source C++ solver compiled and called by PuLP to find the mathematical optimum.

## Optimization Pipeline Flow

1. **Feasibility Check**: Before running the solver, a pre-check validates if the required charge can physically be achieved within the timeframe given the `max_charge_rate_kw`.
2. **Setup Variables**: Continuous LP variables are constructed for each hour. If V2G is enabled, a set of discharge variables is also instantiated.
3. **Solve**: The model constraints and objective function are fed to CBC.
4. **Schedule Extraction**: The solver outputs the exact charging/discharging sequence which is then mapped to cost summaries and battery health models.
