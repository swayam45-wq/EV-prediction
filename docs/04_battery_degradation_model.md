# 04. Battery Degradation Model

The system doesn't just look at cost; it evaluates how a charging session impacts long-term battery health. This logic is in `backend/services/battery_degradation.py`.

In Phase 1, this is a **heuristic, rule-based model** that calculates a "Wear Score" from 0 to 100. In Phase 2, this will be replaced by a Machine Learning model trained on real-world battery data.

## Wear Score Components (Max 100 points)

The total score is the sum of three penalties. A higher score means more battery wear.

### 1. Temperature Impact (Max 40 points)
Lithium-ion batteries have a "Goldilocks" zone (roughly 15°C to 25°C).
*   **Heat Penalty:** Based loosely on the Arrhenius equation. Chemical reaction rates (and degradation mechanisms like SEI layer growth) increase exponentially with temperature. The penalty doubles for roughly every 10°C above 25°C.
*   **Cold Penalty:** Charging a cold battery can cause lithium plating, permanently damaging the cell. A linear penalty is applied for temperatures below 15°C, increasing sharply below 0°C.

### 2. High SoC Stress (Max 35 points)
Holding a battery at a very high State of Charge (SoC) increases internal voltage stress, accelerating calendar aging and SEI layer growth.
*   **0% - 80%:** No penalty. This is the optimal operating range.
*   **80% - 90%:** Moderate linear penalty.
*   **90% - 100%:** Severe linear penalty. Charging to 100% daily is strongly discouraged.

### 3. Fast Charging Penalty (Max 25 points)
Fast charging generates excessive heat and mechanical stress within the battery cells. This is measured via C-rate.
*   **C-rate = Charging Power (kW) / Battery Capacity (kWh)**
*   Example: Charging a 75 kWh battery at 11 kW is a C-rate of ~0.15C (very slow). Charging at 150 kW is 2.0C (very fast).
*   **<= 0.5C:** No penalty.
*   **0.5C - 1.0C:** Moderate linear penalty.
*   **> 1.0C:** Severe penalty.

## Recommendations Generation

Based on the calculated sub-scores, the model generates specific, actionable advice.
*   If the target SoC is 95%, it will warn the user to lower it to 80% for daily driving.
*   If the temperature is 38°C, it will suggest charging during cooler nighttime hours.
*   If the C-rate is high, it suggests using Level 2 AC charging when time permits.
