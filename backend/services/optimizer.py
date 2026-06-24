"""
LP-Based EV Charging & V2G Schedule Optimizer — Phase 4.

Uses PuLP with the CBC solver to find the minimum-cost charging
schedule subject to energy delivery, departure time, and battery
capacity constraints.

Phase 4 adds V2G (Vehicle-to-Grid) support:
  - Decision variables for both charging AND discharging
  - Discharge revenue reduces total cost
  - SoC continuity constraint across all slots
  - Minimum departure SoC guarantee

LP Formulation (V2G-extended):
    Decision Variables:
        c[t] = energy charged  (kWh) in slot t  ≥ 0
        d[t] = energy discharged (kWh) in slot t ≥ 0   (V2G only)

    Objective:
        Minimize  Σ price[t] × c[t]  −  Σ v2g_rate[t] × d[t]
                 t∈T                   t∈V2G_slots

    Constraints:
        1. SoC[t] = SoC[t-1] + c[t]×efficiency − d[t]/efficiency
        2. SoC_min ≤ SoC[t] ≤ usable_capacity   ∀ t
        3. 0 ≤ c[t] ≤ max_charge_rate_kw
        4. 0 ≤ d[t] ≤ max_discharge_rate_kw      (V2G slots only)
        5. SoC[departure_slot] ≥ target_energy_needed
        6. c[t] and d[t] cannot both be non-zero  (big-M relaxed)
"""

import pulp
import shutil
import os
from typing import Optional


def optimize_charging_schedule(
    hours: list[str],
    prices: list[float],
    max_charge_rate_kw: float,
    battery_capacity_kwh: float,
    current_soc_pct: float,
    target_soc_pct: float,
    battery_health_soh: float = 100.0,
    charging_efficiency: float = 0.90,
    temperature_celsius: float = 25.0,
    solver_time_limit: int = 30,
    # V2G parameters (Phase 4)
    v2g_enabled: bool = False,
    v2g_max_discharge_kw: Optional[float] = None,
    v2g_rate_multiplier: float = 0.85,  # fraction of grid price paid for V2G
    v2g_min_soc_pct: float = 20.0,      # never discharge below this
) -> dict:
    """
    Solve the optimal charging (and optional V2G discharge) schedule.

    Args:
        hours: List of hour labels (e.g., ["00:00", "01:00", ...])
        prices: Electricity price ($/kWh) for each hour slot
        max_charge_rate_kw: Maximum charger power (kW)
        battery_capacity_kwh: Total battery capacity (kWh)
        current_soc_pct: Current state of charge (0-100)
        target_soc_pct: Target state of charge (0-100)
        battery_health_soh: Battery health percentage (0-100)
        charging_efficiency: Wall-to-battery efficiency (0.0-1.0)
        temperature_celsius: Ambient temperature (°C)
        solver_time_limit: Max solver runtime in seconds
        v2g_enabled: Enable Vehicle-to-Grid discharge scheduling
        v2g_max_discharge_kw: Max discharge power (defaults to max_charge_rate_kw)
        v2g_rate_multiplier: Fraction of grid price paid for V2G energy
        v2g_min_soc_pct: Minimum SoC to maintain during V2G discharge

    Returns:
        Dictionary with schedule, status, costs, and V2G revenue
    """
    n = len(hours)
    if n == 0:
        return {"status": "error", "schedule": [], "total_cost": 0.0}

    # ── Derived constants ─────────────────────────────────────
    usable_capacity_kwh = battery_capacity_kwh * (battery_health_soh / 100.0)
    current_energy_kwh  = usable_capacity_kwh * (current_soc_pct / 100.0)
    target_energy_kwh   = usable_capacity_kwh * (target_soc_pct / 100.0)
    energy_needed       = max(0.0, target_energy_kwh - current_energy_kwh)
    v2g_min_energy_kwh  = usable_capacity_kwh * (v2g_min_soc_pct / 100.0)

    # Temperature efficiency penalty
    temp_eff = charging_efficiency
    if temperature_celsius > 35:
        temp_eff *= 0.92
    elif temperature_celsius < 0:
        temp_eff *= 0.82
    elif temperature_celsius < 5:
        temp_eff *= 0.90

    # ── Already charged? ──────────────────────────────────────
    if energy_needed <= 0.01:
        schedule = [{
            "hour": h, "price": p, "energy_kwh": 0.0,
            "is_charging": False, "cumulative_soc": current_soc_pct,
            "is_discharging": False, "discharge_kwh": 0.0,
        } for h, p in zip(hours, prices)]
        return {
            "status": "optimal",
            "schedule": schedule,
            "total_cost": 0.0,
            "total_energy_kwh": 0.0,
            "v2g_revenue": 0.0,
            "net_cost": 0.0,
        }

    # ── Solver setup ──────────────────────────────────────────
    solver = _get_solver(solver_time_limit)
    prob = pulp.LpProblem("ev_charging_v2g", pulp.LpMinimize)

    # Decision variables — charge per slot
    c = [pulp.LpVariable(f"c_{t}", lowBound=0, upBound=max_charge_rate_kw)
         for t in range(n)]

    # V2G discharge variables
    if v2g_enabled:
        max_d_kw = v2g_max_discharge_kw or max_charge_rate_kw
        d = [pulp.LpVariable(f"d_{t}", lowBound=0, upBound=max_d_kw)
             for t in range(n)]
        v2g_rates = [p * v2g_rate_multiplier for p in prices]
    else:
        d = [pulp.LpVariable(f"d_{t}", lowBound=0, upBound=0) for t in range(n)]
        v2g_rates = [0.0] * n

    # SoC energy state at end of each slot
    soc_e = [pulp.LpVariable(f"soc_{t}", lowBound=0, upBound=usable_capacity_kwh)
             for t in range(n)]

    # ── Objective: min cost − V2G revenue ────────────────────
    charge_cost   = pulp.lpSum(prices[t] * c[t] for t in range(n))
    v2g_revenue_lp = pulp.lpSum(v2g_rates[t] * d[t] for t in range(n))
    prob += charge_cost - v2g_revenue_lp, "minimize_net_cost"

    # ── Constraints ───────────────────────────────────────────

    # SoC continuity: soc[t] = soc[t-1] + charge×eff − discharge/eff
    for t in range(n):
        prev_soc = current_energy_kwh if t == 0 else soc_e[t - 1]
        prob += (
            soc_e[t] == prev_soc
                + c[t] * temp_eff
                - (d[t] / temp_eff if v2g_enabled else 0),
            f"soc_continuity_{t}",
        )

    # SoC floor (never go below minimum)
    if v2g_enabled:
        for t in range(n):
            prob += soc_e[t] >= v2g_min_energy_kwh, f"min_soc_{t}"

    # Must reach target by last eligible slot
    prob += (
        pulp.lpSum(c[t] * temp_eff - (d[t] / temp_eff if v2g_enabled else 0)
                   for t in range(n))
        >= energy_needed,
        "energy_delivery",
    )

    # Total charge ≤ remaining capacity
    max_deliverable = usable_capacity_kwh - current_energy_kwh
    prob += (
        pulp.lpSum(c[t] * temp_eff for t in range(n)) <= max_deliverable * 1.01,
        "capacity_ceiling",
    )

    # Warm/cool temperature penalty: reduce max charge rate
    if temperature_celsius > 38 or temperature_celsius < -5:
        rate_limit = max_charge_rate_kw * 0.7
        for t in range(n):
            prob += c[t] <= rate_limit, f"temp_derate_{t}"

    # ── Solve ─────────────────────────────────────────────────
    status_code = prob.solve(solver)
    status_str  = pulp.LpStatus[status_code]

    if status_str != "Optimal":
        return {
            "status":         "infeasible",
            "schedule":       [],
            "total_cost":     0.0,
            "total_energy_kwh": 0.0,
            "v2g_revenue":    0.0,
            "net_cost":       0.0,
        }

    # ── Build schedule ────────────────────────────────────────
    schedule = []
    cum_energy = current_energy_kwh

    for t in range(n):
        c_val = max(0.0, pulp.value(c[t]) or 0.0)
        d_val = max(0.0, pulp.value(d[t]) or 0.0) if v2g_enabled else 0.0

        cum_energy += c_val * temp_eff - (d_val / temp_eff if v2g_enabled else 0)
        cum_energy  = max(0.0, min(cum_energy, usable_capacity_kwh))
        cum_soc     = (cum_energy / usable_capacity_kwh) * 100.0

        schedule.append({
            "hour":            hours[t],
            "price":           round(prices[t], 4),
            "energy_kwh":      round(c_val, 4),
            "is_charging":     c_val > 0.01,
            "cumulative_soc":  round(min(cum_soc, 100.0), 1),
            "is_discharging":  d_val > 0.01,
            "discharge_kwh":   round(d_val, 4),
        })

    total_charge_cost = sum(prices[t] * (pulp.value(c[t]) or 0.0) for t in range(n))
    total_v2g_revenue = sum(v2g_rates[t] * (pulp.value(d[t]) or 0.0) for t in range(n))
    total_energy      = sum(s["energy_kwh"] for s in schedule)

    return {
        "status":           "optimal",
        "schedule":         schedule,
        "total_cost":       round(total_charge_cost, 5),
        "total_energy_kwh": round(total_energy, 3),
        "v2g_revenue":      round(total_v2g_revenue, 5),
        "net_cost":         round(total_charge_cost - total_v2g_revenue, 5),
        "v2g_enabled":      v2g_enabled,
    }


def _get_solver(time_limit: int):
    """Return CBC solver if available, else PuLP default."""
    if shutil.which("cbc"):
        return pulp.COIN_CMD(msg=0, timeLimit=time_limit)
    cbc_path = os.path.join(os.path.dirname(pulp.__file__), "solverdir", "cbc")
    if os.path.isfile(cbc_path):
        return pulp.COIN_CMD(path=cbc_path, msg=0, timeLimit=time_limit)
    return pulp.PULP_CBC_CMD(msg=0, timeLimit=time_limit)
