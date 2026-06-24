"""
Enhanced AI Explanation Engine — Phase 4.

Generates rich, context-aware natural-language explanations for
every charging decision. No LLM API key required — uses a
deterministic rule-based reasoning engine that mirrors how a
domain expert would explain the schedule.

Key improvements over Phase 1:
  - Multi-factor reasoning (cost + health + weather + V2G all together)
  - Quantified claims ("saving $0.42 vs charging now")
  - Comparisons against naive baseline
  - Progressive explanations: strategy → schedule → health → savings
  - Battery physics references where relevant
"""

from __future__ import annotations
from typing import Optional


def generate_explanations(
    *,
    current_soc: float,
    target_soc: float,
    battery_capacity_kwh: float,
    battery_health_soh: float,
    max_charge_rate_kw: float,
    departure_time: str,
    temperature_celsius: float,
    weather_condition: str,
    start_charging: Optional[str],
    stop_charging: Optional[str],
    total_energy_kwh: Optional[float],
    normal_cost: Optional[float],
    optimized_cost: Optional[float],
    savings_dollar: Optional[float],
    savings_percent: Optional[float],
    peak_price: Optional[float],
    off_peak_price: Optional[float],
    off_peak_hour: Optional[str],
    wear_score: Optional[float],
    wear_rating: Optional[str],
    schedule_slots: Optional[list[dict]] = None,
    v2g_enabled: bool = False,
    v2g_revenue: Optional[float] = None,
) -> list[str]:
    """
    Generate a ranked list of human-readable explanations.

    Returns up to 7 explanations, ordered from most to least important.
    Each is a single concise sentence (≤ 140 chars) suitable for display
    as a bullet point in the dashboard.
    """
    explanations: list[str] = []
    energy_needed = (target_soc - current_soc) / 100 * battery_capacity_kwh

    # ── 1. Core strategy ─────────────────────────────────────
    if start_charging and stop_charging:
        window_desc = _time_window(start_charging, stop_charging)
        if savings_percent and savings_percent > 5:
            explanations.append(
                f"Charging scheduled {window_desc} to exploit off-peak rates "
                f"(saving {savings_percent:.1f}% vs charging immediately)."
            )
        else:
            explanations.append(
                f"Charging window set {window_desc} — earliest slot that "
                f"delivers {energy_needed:.1f} kWh before {departure_time}."
            )
    else:
        explanations.append(
            f"No feasible schedule found — {energy_needed:.1f} kWh needed but "
            f"insufficient time before {departure_time}."
        )
        return explanations

    # ── 2. Price reasoning ────────────────────────────────────
    if peak_price and off_peak_price and off_peak_hour:
        price_ratio = peak_price / off_peak_price if off_peak_price > 0 else 1
        if price_ratio > 1.5:
            explanations.append(
                f"Peak price (${peak_price:.3f}/kWh) is {price_ratio:.1f}× "
                f"off-peak (${off_peak_price:.3f}/kWh at {off_peak_hour}) — "
                f"optimizer avoids peak hours entirely."
            )
        elif off_peak_price:
            explanations.append(
                f"Cheapest slot at {off_peak_hour} (${off_peak_price:.3f}/kWh) "
                f"prioritised for bulk charging."
            )

    # ── 3. Cost savings ───────────────────────────────────────
    if savings_dollar and savings_dollar > 0.001:
        if normal_cost and optimized_cost:
            explanations.append(
                f"Cost reduced from ${normal_cost:.3f} → ${optimized_cost:.3f} "
                f"(saving ${savings_dollar:.3f} this session)."
            )

    # ── 4. Battery health reasoning ───────────────────────────
    if wear_score is not None and wear_rating:
        if wear_rating == "Low":
            explanations.append(
                f"Wear score {wear_score:.0f}/100 (Low) — schedule avoids "
                f"fast charging and high-SoC stress. Optimal for battery longevity."
            )
        elif wear_rating == "Medium":
            explanations.append(
                f"Wear score {wear_score:.0f}/100 (Medium) — consider capping "
                f"target SoC at 80% to reduce electrochemical stress."
            )
        else:
            explanations.append(
                f"Wear score {wear_score:.0f}/100 (High) — temperature or "
                f"C-rate is elevated. Battery health tip: charge slower or cooler."
            )

    # ── 5. Temperature / weather ──────────────────────────────
    if temperature_celsius > 35:
        explanations.append(
            f"Ambient temp {temperature_celsius}°C — thermal management "
            f"reduces effective charge rate. Night charging recommended."
        )
    elif temperature_celsius < 0:
        explanations.append(
            f"Freezing conditions ({temperature_celsius}°C) — lithium plating "
            f"risk below 0°C. Keep C-rate ≤ 0.5C until battery warms up."
        )

    if weather_condition.lower() in ("clear", "sunny") and temperature_celsius < 35:
        explanations.append(
            "Clear skies today — if solar panels available, "
            "midday (10 AM–2 PM) self-charging is most economical."
        )

    # ── 6. SoH degradation note ───────────────────────────────
    if battery_health_soh < 85:
        usable_kwh = battery_capacity_kwh * (battery_health_soh / 100)
        explanations.append(
            f"Battery SoH is {battery_health_soh:.0f}% — usable capacity is "
            f"~{usable_kwh:.1f} kWh (down from {battery_capacity_kwh:.0f} kWh nominal)."
        )

    # ── 7. V2G revenue ────────────────────────────────────────
    if v2g_enabled and v2g_revenue and v2g_revenue > 0:
        explanations.append(
            f"V2G discharge during peak hours earns ~${v2g_revenue:.3f} "
            f"grid revenue, partially offsetting your charging cost."
        )

    # ── 8. Active charging slot count ────────────────────────
    if schedule_slots:
        active = sum(1 for s in schedule_slots if s.get("is_charging"))
        if active > 0:
            explanations.append(
                f"Charger active for {active} of 24 hours — "
                f"remaining {24 - active} hours are off to minimise cost and wear."
            )

    return explanations[:8]


def generate_health_advice(
    *,
    target_soc: float,
    temperature_celsius: float,
    max_charge_rate_kw: float,
    battery_capacity_kwh: float,
    battery_health_soh: float,
    wear_rating: str,
    weather_condition: str,
) -> list[str]:
    """
    Generate actionable battery health advice tailored to this session.
    Returns up to 5 tips specific to the user's current inputs.
    """
    tips: list[str] = []
    c_rate = max_charge_rate_kw / battery_capacity_kwh

    # SoC ceiling advice
    if target_soc > 90:
        tips.append(
            f"Charging to {target_soc:.0f}% accelerates cathode degradation. "
            "Cap daily charging at 80% unless you need full range."
        )
    elif target_soc > 80:
        tips.append(
            "Above 80% SoC increases lithium plating stress. "
            "Reserve 90–100% for long-distance days only."
        )

    # Fast charging advice
    if c_rate > 1.5:
        tips.append(
            f"C-rate of {c_rate:.1f}C is high. Limit DC fast charging to "
            "once per day to preserve cathode crystal structure."
        )
    elif c_rate > 0.8:
        tips.append(
            f"C-rate {c_rate:.2f}C — moderate. Level 2 (≤ 0.5C) preserves "
            "battery longer for daily use."
        )

    # Temperature advice
    if temperature_celsius > 38:
        tips.append(
            "Park in shade or a garage during charging in hot weather — "
            "ambient heat is the #1 long-term battery killer."
        )
    elif temperature_celsius < 5:
        tips.append(
            "Pre-warm the battery with cabin pre-conditioning before charging "
            "in cold weather to protect cell chemistry."
        )

    # SoH degradation
    if battery_health_soh < 80:
        tips.append(
            f"SoH at {battery_health_soh:.0f}% — consider a battery health "
            "diagnostic check at your nearest service centre."
        )
    elif battery_health_soh < 90:
        tips.append(
            "Moderate SoH — reduce fast charging frequency and avoid "
            "leaving the battery below 15% or above 85% for extended periods."
        )

    # General best practice if no specific warnings
    if not tips:
        tips.append(
            "Conditions look ideal. Maintain SoC between 20–80% daily for "
            "maximum long-term battery lifespan."
        )

    return tips[:5]


# ── Helpers ───────────────────────────────────────────────────

def _time_window(start: str, stop: str) -> str:
    """Format a charging window as a readable string."""
    return f"from {start} to {stop}"
