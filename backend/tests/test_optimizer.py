"""
Tests for the LP Charging Optimizer.

Verifies that the optimizer produces correct, feasible schedules
under various scenarios including normal operation, edge cases,
and infeasible inputs.
"""

import pytest
from services.optimizer import optimize_charging_schedule


class TestOptimizerBasic:
    """Basic optimization scenarios."""

    def test_optimal_schedule_cheapest_hours(self):
        """Optimizer should concentrate charging in the cheapest hours."""
        result = optimize_charging_schedule(
            hours=["00:00", "01:00", "02:00", "03:00", "04:00", "05:00", "06:00", "07:00"],
            prices=[0.12, 0.10, 0.08, 0.07, 0.08, 0.10, 0.15, 0.22],
            max_charge_rate_kw=11.0,
            battery_capacity_kwh=75.0,
            current_soc_pct=35.0,
            target_soc_pct=80.0,
            battery_health_soh=92.0,
        )

        assert result["status"] == "optimal"
        assert result["total_cost"] is not None
        assert result["total_cost"] > 0
        assert result["total_energy_kwh"] > 0
        assert len(result["schedule"]) == 8

        # The cheapest slot (03:00 at $0.07) should have the most energy
        slot_03 = result["schedule"][3]
        assert slot_03["energy_kwh"] > 0, "Cheapest slot should be used for charging"

    def test_sufficient_energy_delivered(self):
        """Optimizer must deliver enough energy to reach target SoC."""
        result = optimize_charging_schedule(
            hours=["00:00", "01:00", "02:00", "03:00"],
            prices=[0.10, 0.10, 0.10, 0.10],
            max_charge_rate_kw=11.0,
            battery_capacity_kwh=75.0,
            current_soc_pct=50.0,
            target_soc_pct=80.0,
            battery_health_soh=100.0,
            charging_efficiency=0.90,
        )

        assert result["status"] == "optimal"

        # Energy needed: (0.80 - 0.50) * 75 = 22.5 kWh at battery
        # Wall energy needed: 22.5 / 0.90 = 25.0 kWh
        total_energy = sum(s["energy_kwh"] for s in result["schedule"])
        energy_delivered = total_energy * 0.90  # Battery receives this

        assert energy_delivered >= 22.4, (
            f"Must deliver ≥22.5 kWh, got {energy_delivered:.2f} kWh"
        )

    def test_already_charged(self):
        """If current SoC >= target SoC, no charging is needed."""
        result = optimize_charging_schedule(
            hours=["00:00", "01:00"],
            prices=[0.10, 0.10],
            max_charge_rate_kw=11.0,
            battery_capacity_kwh=75.0,
            current_soc_pct=85.0,
            target_soc_pct=80.0,
        )

        assert result["status"] == "optimal"
        total_energy = sum(s["energy_kwh"] for s in result["schedule"])
        assert total_energy == 0, "No energy should be charged"


class TestOptimizerEdgeCases:
    """Edge cases and boundary conditions."""

    def test_infeasible_not_enough_time(self):
        """Infeasible when max energy < required energy."""
        result = optimize_charging_schedule(
            hours=["00:00"],  # Only 1 hour
            prices=[0.10],
            max_charge_rate_kw=7.0,  # 7 kW × 1 hour × 0.9 = 6.3 kWh
            battery_capacity_kwh=75.0,
            current_soc_pct=10.0,
            target_soc_pct=90.0,   # Needs (0.9-0.1)*75 = 60 kWh
        )

        assert result["status"] == "infeasible"

    def test_uniform_prices(self):
        """With uniform prices, any valid schedule should have equal cost."""
        result = optimize_charging_schedule(
            hours=["00:00", "01:00", "02:00", "03:00"],
            prices=[0.10, 0.10, 0.10, 0.10],
            max_charge_rate_kw=11.0,
            battery_capacity_kwh=60.0,
            current_soc_pct=60.0,
            target_soc_pct=80.0,
        )

        assert result["status"] == "optimal"
        assert result["total_energy_kwh"] > 0

    def test_single_slot(self):
        """Should work with just one hourly slot if feasible."""
        result = optimize_charging_schedule(
            hours=["03:00"],
            prices=[0.08],
            max_charge_rate_kw=11.0,
            battery_capacity_kwh=50.0,
            current_soc_pct=70.0,
            target_soc_pct=80.0,  # Needs (0.1)*50 = 5 kWh
            charging_efficiency=0.90,
        )

        assert result["status"] == "optimal"
        assert result["total_energy_kwh"] > 0

    def test_soh_reduces_usable_capacity(self):
        """Degraded battery (low SOH) means less usable capacity."""
        # 50% SOH → usable capacity = 75 * 0.50 = 37.5 kWh
        result = optimize_charging_schedule(
            hours=["00:00", "01:00", "02:00", "03:00"],
            prices=[0.10, 0.10, 0.10, 0.10],
            max_charge_rate_kw=11.0,
            battery_capacity_kwh=75.0,
            current_soc_pct=50.0,
            target_soc_pct=80.0,
            battery_health_soh=50.0,  # Degraded battery
        )

        assert result["status"] == "optimal"
        # Energy needed = (0.80 - 0.50) * 37.5 = 11.25 kWh
        total_energy = sum(s["energy_kwh"] for s in result["schedule"])
        assert total_energy < 20, "Degraded battery needs less wall energy"


class TestOptimizerCostMinimization:
    """Verify the optimizer actually minimizes cost."""

    def test_prefers_cheap_slots(self):
        """More energy should be allocated to cheaper slots."""
        result = optimize_charging_schedule(
            hours=["00:00", "01:00", "02:00", "03:00"],
            prices=[0.30, 0.05, 0.05, 0.30],  # Middle slots are cheap
            max_charge_rate_kw=11.0,
            battery_capacity_kwh=60.0,
            current_soc_pct=50.0,
            target_soc_pct=70.0,
            charging_efficiency=0.90,
        )

        assert result["status"] == "optimal"

        # Cheap slots (01:00, 02:00) should have more energy than expensive ones
        schedule = result["schedule"]
        cheap_energy = schedule[1]["energy_kwh"] + schedule[2]["energy_kwh"]
        expensive_energy = schedule[0]["energy_kwh"] + schedule[3]["energy_kwh"]

        assert cheap_energy >= expensive_energy, (
            f"Cheap slots ({cheap_energy:.2f} kWh) should have at least as much "
            f"energy as expensive slots ({expensive_energy:.2f} kWh)"
        )

    def test_start_and_stop_times(self):
        """Start and stop times should reflect actual charging activity."""
        result = optimize_charging_schedule(
            hours=["00:00", "01:00", "02:00", "03:00", "04:00"],
            prices=[0.20, 0.20, 0.05, 0.05, 0.20],
            max_charge_rate_kw=11.0,
            battery_capacity_kwh=50.0,
            current_soc_pct=70.0,
            target_soc_pct=80.0,
            charging_efficiency=0.90,
        )

        assert result["status"] == "optimal"
        # Phase 4: start/stop are derived from schedule in the route layer
        active = [s for s in result["schedule"] if s["is_charging"]]
        assert len(active) > 0, "At least one charging slot expected"
        # Cheapest hours are 02:00 and 03:00 — optimizer should pick those
        active_hours = [s["hour"] for s in active]
        assert "02:00" in active_hours or "03:00" in active_hours
