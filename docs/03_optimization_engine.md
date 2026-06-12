# 03. Optimization Engine

The core intelligence of the application resides in `backend/services/optimizer.py`. We use **Linear Programming (LP)** to solve the charging scheduling problem.

## What is Linear Programming?

Linear programming is a mathematical method for determining a way to achieve the best outcome (such as lowest cost) in a given mathematical model given some list of requirements represented as linear relationships.

## Our Formulation

### 1. Decision Variables
The solver must decide how much energy to put into the battery during each hourly slot.
*   $x_t$: Energy charged (in kWh) during time slot $t$.
*   These variables are continuous and bounded: $0 \leq x_t \leq \text{MaxChargeRate}$.

### 2. Objective Function
Our primary goal is to minimize cost. However, to gently guide the solver away from charging during extreme heat (which degrades the battery), we add a small "penalty" cost to slots during high-temperature hours.

*   **Minimize:** $\sum (Price_t + Penalty_t) \times x_t$

### 3. Constraints
The solver must obey the physical realities of the vehicle and the user's schedule:

*   **Energy Target Constraint:** The total energy charged, multiplied by the charging efficiency, must equal or exceed the energy needed to reach the target SoC.
    *   $\sum (x_t \times \text{Efficiency}) \geq \text{EnergyNeeded}$
*   **Battery Capacity Constraint:** The cumulative energy in the battery at any time slot $t$ cannot exceed the battery's total usable capacity.
    *   $\text{CurrentEnergy} + \sum_{i=0}^{t} (x_i \times \text{Efficiency}) \leq \text{UsableCapacity}$
*   **Time Constraint:** The solver is only given variables ($x_t$) for time slots that occur *before* the user's specified departure time.

## Technology: PuLP and CBC

*   **PuLP:** A Python library used to define LP problems in an intuitive, pythonic way. It acts as an interface.
*   **CBC (COIN-OR Branch and Cut):** The underlying open-source solver written in C++ that actually performs the mathematical optimization.

## How the Code Works

1.  **Preparation:** The function calculates the `energy_needed` based on current SoC, target SoC, battery capacity, and State of Health (SoH).
2.  **Feasibility Check:** Before running the solver, it quickly checks if it's physically possible to deliver the required energy within the available time given the maximum charge rate.
3.  **Problem Definition:** It initializes the `pulp.LpProblem` and creates the decision variables (`pulp.LpVariable`).
4.  **Constraint Addition:** The objective function and constraints are added to the problem using `pulp.lpSum`.
5.  **Solving:** The `_get_solver` helper function locates the CBC executable and runs the optimization.
6.  **Extraction:** If the status is optimal, it iterates through the solved variables (`charge[t].varValue`) to build the final schedule.
