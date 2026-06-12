"""
AI Recommendation Engine.

Generates human-readable explanations for each scheduling decision
made by the optimizer. In Phase 1 this uses rule-based logic;
in Phase 2 it can be swapped for an LLM (OpenAI / local).
"""


def generate_explanations(
    schedule: list[dict],
    prices: list[float],
    temperature_celsius: float,
    target_soc_pct: float,
    current_soc_pct: float,
    cost_analysis: dict,
) -> list[str]:
    """
    Generate human-readable explanations for the charging plan.

    Analyzes the optimizer's output and produces clear, actionable
    explanations that help the user understand WHY the schedule
    was chosen.

    Args:
        schedule: List of hourly charging slots from the optimizer
        prices: Raw electricity prices per slot
        temperature_celsius: Ambient temperature
        target_soc_pct: Target state of charge (0-100)
        current_soc_pct: Current state of charge (0-100)
        cost_analysis: Cost comparison from cost_analyzer

    Returns:
        List of explanation strings.
    """
    explanations = []

    if not schedule:
        return ["No charging schedule was generated."]

    # --- 1. Identify active charging hours ---
    active_slots = [s for s in schedule if s.get("is_charging", False)]
    if not active_slots:
        explanations.append(
            "🔋 Your battery is already at or above the target charge. "
            "No charging is needed."
        )
        return explanations

    # --- 2. Explain timing choice ---
    first_slot = active_slots[0]
    last_slot = active_slots[-1]
    explanations.append(
        f"⏰ Charging scheduled from {first_slot['hour']} to {last_slot['hour']}."
    )

    # --- 3. Explain price optimization ---
    avg_active_price = sum(s["price"] for s in active_slots) / len(active_slots)
    avg_all_price = sum(prices) / len(prices) if prices else 0

    if avg_active_price < avg_all_price:
        savings_pct = (1 - avg_active_price / avg_all_price) * 100
        explanations.append(
            f"💰 Charging was shifted to hours when electricity prices are "
            f"{savings_pct:.0f}% below average "
            f"(avg ${avg_active_price:.3f}/kWh vs ${avg_all_price:.3f}/kWh)."
        )

    # Find the cheapest hour being used
    cheapest_active = min(active_slots, key=lambda s: s["price"])
    explanations.append(
        f"📉 The cheapest charging slot is {cheapest_active['hour']} "
        f"at ${cheapest_active['price']:.3f}/kWh."
    )

    # --- 4. Explain cost savings ---
    if cost_analysis:
        savings = cost_analysis.get("savings_percent", 0)
        if savings > 0:
            explanations.append(
                f"💵 This optimized schedule saves you "
                f"${cost_analysis['savings_dollar']:.2f} "
                f"({savings:.1f}%) compared to charging immediately."
            )

    # --- 5. Temperature-related explanation ---
    if temperature_celsius > 35:
        explanations.append(
            f"🌡️ Ambient temperature is {temperature_celsius}°C — "
            "the optimizer avoided peak-heat hours to reduce battery degradation."
        )
    elif temperature_celsius < 5:
        explanations.append(
            f"❄️ Low temperature ({temperature_celsius}°C) detected — "
            "consider pre-conditioning your battery before charging begins."
        )

    # --- 6. SoC-related explanation ---
    if target_soc_pct <= 80:
        explanations.append(
            f"🔋 Target charge is set to {target_soc_pct:.0f}%, which is "
            "optimal for long-term battery health."
        )
    elif target_soc_pct > 90:
        explanations.append(
            f"⚠️ Target charge is {target_soc_pct:.0f}% — charging above 90% "
            "accelerates battery degradation. Consider 80% for daily use."
        )

    # --- 7. Energy summary ---
    total_energy = sum(s["energy_kwh"] for s in active_slots)
    soc_gain = target_soc_pct - current_soc_pct
    explanations.append(
        f"⚡ Total energy to charge: {total_energy:.1f} kWh "
        f"(SoC: {current_soc_pct:.0f}% → {target_soc_pct:.0f}%, "
        f"+{soc_gain:.0f}% gain)."
    )

    return explanations
