"""
Cost Analyzer Service.

Compares the optimized charging schedule against a naive baseline
(charge immediately at whatever prices are available) to quantify
the dollar and percentage savings.
"""


def analyze_costs(
    hours: list[str],
    prices: list[float],
    optimized_energy: list[float],
    energy_needed_kwh: float,
    max_charge_rate_kw: float,
    charging_efficiency: float = 0.90,
) -> dict:
    """
    Compare optimized vs. naive charging costs.

    Naive strategy: start charging immediately at max rate until
    the target energy is delivered (no price optimization).

    Args:
        hours: Hour labels for each slot
        prices: Electricity price per slot ($/kWh)
        optimized_energy: Energy charged per slot from the optimizer (kWh)
        energy_needed_kwh: Total energy to deliver to the battery (kWh)
        max_charge_rate_kw: Maximum charger power (kW)
        charging_efficiency: Wall-to-battery efficiency

    Returns:
        Dictionary with normal_cost, optimized_cost, savings_dollar,
        savings_percent.
    """

    # --- Optimized cost ---
    optimized_cost = sum(
        price * energy
        for price, energy in zip(prices, optimized_energy)
    )

    # --- Naive cost (charge immediately at max rate) ---
    naive_cost = _calculate_naive_cost(
        prices, energy_needed_kwh, max_charge_rate_kw, charging_efficiency
    )

    # --- Savings ---
    savings_dollar = naive_cost - optimized_cost
    savings_percent = (
        (savings_dollar / naive_cost * 100.0) if naive_cost > 0 else 0.0
    )

    return {
        "normal_cost": round(naive_cost, 2),
        "optimized_cost": round(optimized_cost, 2),
        "savings_dollar": round(max(0, savings_dollar), 2),
        "savings_percent": round(max(0, savings_percent), 1),
    }


def _calculate_naive_cost(
    prices: list[float],
    energy_needed_kwh: float,
    max_charge_rate_kw: float,
    charging_efficiency: float,
) -> float:
    """
    Calculate cost of naive "charge immediately" strategy.

    Charges at max rate starting from the first slot until the
    required energy is delivered. No price optimization.
    """
    remaining = energy_needed_kwh  # Energy to deliver to battery
    total_cost = 0.0

    for price in prices:
        if remaining <= 0:
            break

        # Wall energy needed to deliver 'deliverable' to battery
        deliverable = max_charge_rate_kw * charging_efficiency
        actual_delivered = min(deliverable, remaining)
        wall_energy = actual_delivered / charging_efficiency

        total_cost += price * wall_energy
        remaining -= actual_delivered

    return total_cost
