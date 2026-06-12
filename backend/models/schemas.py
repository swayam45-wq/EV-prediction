"""
Pydantic schemas for request validation and response serialization.

All models use Pydantic v2 with Field constraints for automatic
input validation and OpenAPI documentation generation.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ============================================================
# REQUEST MODELS
# ============================================================

class ElectricityPrice(BaseModel):
    """A single hourly electricity price slot."""
    hour: str = Field(
        ...,
        description="Hour label in HH:MM format (e.g., '02:00')",
        examples=["00:00", "01:00", "14:00"],
    )
    price: float = Field(
        ...,
        ge=0.0,
        description="Electricity price in $/kWh for this hour",
        examples=[0.08, 0.12, 0.22],
    )


class ChargingRequest(BaseModel):
    """
    Complete request payload for the /api/recommend endpoint.

    Users provide their vehicle state, schedule, electricity prices,
    and optionally weather data. The system returns an optimized
    charging schedule.
    """

    # --- Vehicle State ---
    current_soc: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Current battery state of charge in percent (0-100)",
        examples=[35.0],
    )
    target_soc: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Desired battery state of charge in percent (0-100)",
        examples=[80.0],
    )
    battery_capacity_kwh: float = Field(
        ...,
        gt=0.0,
        description="Total battery capacity in kWh",
        examples=[75.0],
    )
    max_charge_rate_kw: float = Field(
        ...,
        gt=0.0,
        description="Maximum charging rate in kW (e.g., 7.4 for Level 2, 50+ for DC fast)",
        examples=[11.0],
    )
    battery_health_soh: float = Field(
        default=100.0,
        ge=0.0,
        le=100.0,
        description="Battery State of Health in percent (0-100)",
        examples=[92.0],
    )

    # --- Schedule ---
    departure_time: str = Field(
        ...,
        description="Departure time in HH:MM format (24h clock)",
        examples=["08:00"],
    )

    # --- Electricity Prices ---
    electricity_prices: list[ElectricityPrice] = Field(
        ...,
        min_length=1,
        description="List of hourly electricity price slots covering the charging window",
    )

    # --- Environment (optional) ---
    temperature_celsius: Optional[float] = Field(
        default=25.0,
        description="Ambient temperature in Celsius",
        examples=[28.0, 38.0, -5.0],
    )
    weather_condition: Optional[str] = Field(
        default="clear",
        description="Current weather condition",
        examples=["clear", "sunny", "rain", "snow"],
    )

    # --- Advanced (optional) ---
    charging_efficiency: Optional[float] = Field(
        default=0.90,
        ge=0.5,
        le=1.0,
        description="Wall-to-battery charging efficiency (0.5-1.0)",
    )


# ============================================================
# RESPONSE MODELS
# ============================================================

class HourlyChargingSlot(BaseModel):
    """A single hour in the optimized charging schedule."""
    hour: str = Field(..., description="Hour label (HH:MM)")
    price: float = Field(..., description="Electricity price $/kWh")
    energy_kwh: float = Field(..., description="Energy to charge in this slot (kWh)")
    is_charging: bool = Field(..., description="Whether the charger is active this hour")
    cumulative_soc: float = Field(
        ...,
        description="Projected battery SoC (%) at end of this slot",
    )


class BatteryWearEstimate(BaseModel):
    """Battery degradation risk assessment."""
    total_score: float = Field(..., description="Overall wear score (0-100, lower is better)")
    rating: str = Field(..., description="Risk rating: Low / Medium / High")
    temperature_impact: float = Field(..., description="Points from temperature stress")
    high_soc_stress: float = Field(..., description="Points from high SoC charging")
    fast_charging_penalty: float = Field(..., description="Points from high C-rate")


class CostComparison(BaseModel):
    """Side-by-side cost analysis: naive vs. optimized."""
    normal_cost: float = Field(..., description="Cost if charging immediately ($)")
    optimized_cost: float = Field(..., description="Cost with optimized schedule ($)")
    savings_dollar: float = Field(..., description="Dollar savings")
    savings_percent: float = Field(..., description="Percentage savings")


class ChargingRecommendation(BaseModel):
    """
    Complete response from the /api/recommend endpoint.

    Contains the optimized schedule, cost analysis, battery health
    advice, and human-readable explanations.
    """

    # --- Schedule ---
    status: str = Field(
        ...,
        description="Optimization status: 'optimal', 'infeasible', or 'error'",
    )
    start_charging: Optional[str] = Field(
        None, description="Recommended charging start time (HH:MM)"
    )
    stop_charging: Optional[str] = Field(
        None, description="Recommended charging stop time (HH:MM)"
    )
    schedule: list[HourlyChargingSlot] = Field(
        default_factory=list,
        description="Hour-by-hour charging schedule",
    )

    # --- Energy Summary ---
    total_energy_kwh: Optional[float] = Field(
        None, description="Total energy to be delivered (kWh)"
    )
    target_soc_reached: bool = Field(
        default=False,
        description="Whether the target SoC will be reached",
    )

    # --- Cost ---
    cost_analysis: Optional[CostComparison] = None

    # --- Battery Health ---
    wear_estimate: Optional[BatteryWearEstimate] = None
    battery_health_advice: list[str] = Field(
        default_factory=list,
        description="Actionable battery health recommendations",
    )

    # --- AI Explanations ---
    explanations: list[str] = Field(
        default_factory=list,
        description="Human-readable explanations for scheduling decisions",
    )
