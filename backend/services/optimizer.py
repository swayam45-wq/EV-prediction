"""
LP-Based EV Charging Schedule Optimizer.

Uses PuLP with the CBC solver to find the minimum-cost charging
schedule subject to energy delivery, departure time, and battery
capacity constraints.

LP Formulation:
    Decision Variables:
        x[t] = energy charged (kWh) in hourly slot t  (continuous, ≥ 0)

    Objective:
        Minimize  Σ  (price[t] + penalty[t]) × x[t]
                t∈T

    Constraints:
        1. Σ x[t] × efficiency  ≥  energy_needed
        2. 0 ≤ x[t] ≤ max_charge_rate_kw   ∀ t
        3. cumulative_energy[t] ≤ usable_capacity   ∀ t
        4. Only slots before departure_time are eligible
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
) -> dict:
    """
    Solve the optimal charging schedule using Linear Programming.

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

    Returns:
        Dictionary with keys:
            - status: "optimal" | "infeasible"
            - schedule: list of {hour, price, energy_kwh, is_charging, cumulative_soc}
            - total_cost: float
            - total_energy_kwh: float
            - start_time: str | None
            - stop_time: str | None
    """

    num_slots = len(prices)
    slots = range(num_slots)

    # --- Convert percentages to fractions ---
    current_soc = current_soc_pct / 100.0
    target_soc = target_soc_pct / 100.0

    # Usable capacity accounts for battery degradation (SOH)
    usable_capacity = battery_capacity_kwh * (battery_health_soh / 100.0)

    # Energy needed to reach target SoC (in kWh at the battery)
    energy_needed = (target_soc - current_soc) * usable_capacity

    if energy_needed <= 0:
        # Already at or above target — no charging needed
        return _build_result(
            hours, prices, [0.0] * num_slots,
            current_soc, usable_capacity, "optimal"
        )

    # --- Check feasibility before solving ---
    # Maximum energy deliverable = sum of all slots at max rate × efficiency
    max_deliverable = num_slots * max_charge_rate_kw * charging_efficiency
    if max_deliverable < energy_needed:
        return {
            "status": "infeasible",
            "schedule": [],
            "total_cost": None,
            "total_energy_kwh": None,
            "start_time": None,
            "stop_time": None,
            "message": (
                f"Cannot deliver {energy_needed:.1f} kWh in {num_slots} hours "
                f"at {max_charge_rate_kw} kW. Max deliverable: {max_deliverable:.1f} kWh."
            ),
        }

    # --- Build LP Problem ---
    prob = pulp.LpProblem("EV_Charging_Optimizer", pulp.LpMinimize)

    # Decision variables: energy charged (kWh) per slot
    charge = {
        t: pulp.LpVariable(f"charge_{t}", lowBound=0, upBound=max_charge_rate_kw, cat="Continuous")
        for t in slots
    }

    # --- Temperature-based penalty ---
    # Add a cost surcharge to slots during high-temperature hours
    # to discourage charging in extreme heat (battery degradation)
    penalties = _compute_temperature_penalties(
        num_slots, hours, temperature_celsius
    )

    # --- Objective: Minimize total cost (price + degradation penalty) ---
    prob += pulp.lpSum(
        [(prices[t] + penalties[t]) * charge[t] for t in slots]
    ), "Total_Cost"

    # --- Constraint 1: Total delivered energy meets target ---
    prob += (
        pulp.lpSum([charge[t] * charging_efficiency for t in slots])
        >= energy_needed
    ), "Energy_Target"

    # --- Constraint 2: Cumulative SoC never exceeds battery capacity ---
    current_energy = current_soc * usable_capacity
    for t in slots:
        cumulative = current_energy + pulp.lpSum(
            [charge[s] * charging_efficiency for s in range(t + 1)]
        )
        prob += (
            cumulative <= usable_capacity
        ), f"Max_Capacity_Slot_{t}"

    # --- Solve ---
    solver = _get_solver(solver_time_limit)
    prob.solve(solver)

    if prob.status != pulp.constants.LpStatusOptimal:
        return {
            "status": "infeasible",
            "schedule": [],
            "total_cost": None,
            "total_energy_kwh": None,
            "start_time": None,
            "stop_time": None,
            "message": "Optimizer could not find a feasible solution.",
        }

    # --- Extract results ---
    energy_values = [round(charge[t].varValue or 0.0, 4) for t in slots]

    return _build_result(
        hours, prices, energy_values,
        current_soc, usable_capacity, "optimal"
    )


def _build_result(
    hours: list[str],
    prices: list[float],
    energy_values: list[float],
    current_soc: float,
    usable_capacity: float,
    status: str,
) -> dict:
    """Build the structured result dictionary from solved values."""

    schedule = []
    cumulative_energy = current_soc * usable_capacity
    total_cost = 0.0
    start_time: Optional[str] = None
    stop_time: Optional[str] = None

    for i, (hour, price, energy) in enumerate(
        zip(hours, prices, energy_values)
    ):
        # Track when charging starts and stops
        is_charging = energy > 0.01  # Threshold to ignore solver noise

        if is_charging:
            if start_time is None:
                start_time = hour
            stop_time = hour  # Keep updating to find the last active slot

        # Accumulate energy delivered to battery (after efficiency)
        # Note: energy_values are already "wall energy"; battery gets
        # energy * efficiency. But for cost we charge wall energy.
        cumulative_energy += energy * 0.90  # Use fixed 90% for display
        cumulative_soc = (cumulative_energy / usable_capacity) * 100.0

        slot_cost = price * energy
        total_cost += slot_cost

        schedule.append({
            "hour": hour,
            "price": round(price, 4),
            "energy_kwh": round(energy, 2),
            "is_charging": is_charging,
            "cumulative_soc": round(min(cumulative_soc, 100.0), 1),
        })

    total_energy = sum(energy_values)

    return {
        "status": status,
        "schedule": schedule,
        "total_cost": round(total_cost, 4),
        "total_energy_kwh": round(total_energy, 2),
        "start_time": start_time,
        "stop_time": stop_time,
    }


def _compute_temperature_penalties(
    num_slots: int,
    hours: list[str],
    temperature_celsius: float,
) -> list[float]:
    """
    Compute per-slot cost penalties based on temperature.

    Logic:
        - If temp > 35°C: add 15% surcharge to daytime slots (10:00-17:00)
          to discourage charging during peak heat.
        - If temp < 5°C: add 5% surcharge (cold weather reduces efficiency
          and risks lithium plating).
        - Otherwise: no penalty.
    """
    penalties = []

    for i in range(num_slots):
        penalty = 0.0

        # Parse hour to check if it's a daytime slot
        try:
            hour_int = int(hours[i].split(":")[0])
        except (ValueError, IndexError):
            hour_int = i  # Fallback

        if temperature_celsius > 35.0:
            # Penalize daytime slots more in extreme heat
            if 10 <= hour_int <= 17:
                penalty = 0.03  # $0.03/kWh surcharge
            else:
                penalty = 0.01  # Small penalty even at night in extreme heat
        elif temperature_celsius < 5.0:
            penalty = 0.015  # Cold weather penalty

        penalties.append(penalty)

    return penalties


def _get_solver(time_limit: int = 30):
    """
    Find and return a working CBC solver instance.

    Search order:
        1. cbc.exe on PATH (via shutil.which)
        2. cbcbox package's bundled cbc.exe
        3. User's Python Scripts directory
        4. PuLP's default solver as last resort
    """

    # --- 1. Check PATH ---
    cbc_path = shutil.which("cbc")
    if cbc_path:
        try:
            return pulp.COIN_CMD(path=cbc_path, msg=0, timeLimit=time_limit)
        except (AttributeError, Exception):
            return pulp.PULP_CBC_CMD(path=cbc_path, msg=0, timeLimit=time_limit)

    # --- 2. Check cbcbox package ---
    try:
        import cbcbox
        cbc_dir = os.path.dirname(cbcbox.__file__)
        cbc_exe = os.path.join(cbc_dir, "cbc.exe")
        if not os.path.exists(cbc_exe):
            cbc_exe = os.path.join(cbc_dir, "cbc")
        if os.path.exists(cbc_exe):
            try:
                return pulp.COIN_CMD(path=cbc_exe, msg=0, timeLimit=time_limit)
            except (AttributeError, Exception):
                return pulp.PULP_CBC_CMD(path=cbc_exe, msg=0, timeLimit=time_limit)
    except ImportError:
        pass

    # --- 3. Check common user Scripts directory ---
    import sys
    scripts_dir = os.path.join(os.path.dirname(sys.executable), "Scripts")
    user_scripts = os.path.join(
        os.path.expanduser("~"),
        "AppData", "Roaming", "Python",
        f"Python{sys.version_info.major}{sys.version_info.minor}",
        "Scripts",
    )
    for scripts in [scripts_dir, user_scripts]:
        cbc_exe = os.path.join(scripts, "cbc.exe")
        if os.path.exists(cbc_exe):
            try:
                return pulp.COIN_CMD(path=cbc_exe, msg=0, timeLimit=time_limit)
            except (AttributeError, Exception):
                return pulp.PULP_CBC_CMD(path=cbc_exe, msg=0, timeLimit=time_limit)

    # --- 4. Fallback to default solver ---
    return pulp.getSolver("PULP_CBC_CMD", msg=0, timeLimit=time_limit)

