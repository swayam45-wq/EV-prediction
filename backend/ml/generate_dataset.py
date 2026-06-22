"""
Synthetic Battery Degradation Dataset Generator.

Generates a realistic training dataset of 15,000 charging sessions
with features derived from real-world EV battery research:

Features (inputs):
    - battery_soc_pct          : Current State of Charge (%)
    - target_soc_pct           : Target SoC after charging (%)
    - ambient_temp_c           : Ambient temperature (°C)
    - battery_temp_c           : Battery temperature during charging (°C)
    - charge_rate_kw           : Average charging rate (kW)
    - battery_capacity_kwh     : Battery capacity (kWh)
    - cycle_count              : Cumulative charge cycles
    - battery_health_soh       : State of Health (%)
    - c_rate                   : Charge rate / capacity (derived)
    - soc_delta                : target_soc - battery_soc (derived)

Target (output):
    - wear_score               : Battery wear score (0-100, lower=better)

The wear_score formula is grounded in:
    - Arrhenius temperature degradation model
    - Lithium plating risk at low temps
    - SEI layer growth at high SoC
    - Mechanical stress at high C-rates
    - Calendar aging based on cycle count

Usage:
    python backend/ml/generate_dataset.py
    -> Saves: backend/ml/data/battery_degradation_dataset.csv
"""

import numpy as np
import pandas as pd
import os

# Reproducibility
np.random.seed(42)

N_SAMPLES = 15_000
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "battery_degradation_dataset.csv")


def generate_dataset(n: int = N_SAMPLES) -> pd.DataFrame:
    """Generate a synthetic EV charging session dataset."""

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # --------------------------------------------------------
    # RAW FEATURES (sampled from realistic distributions)
    # --------------------------------------------------------

    # Battery SoC at start of charging (10–90%)
    battery_soc_pct = np.random.uniform(10, 90, n)

    # Target SoC (always >= battery_soc_pct, up to 100%)
    soc_delta_raw = np.random.uniform(5, 70, n)
    target_soc_pct = np.clip(battery_soc_pct + soc_delta_raw, 10, 100)

    # Battery capacity: common EVs range 40–100 kWh
    battery_capacity_kwh = np.random.choice(
        [40, 58, 64, 75, 82, 100],
        n,
        p=[0.10, 0.15, 0.20, 0.25, 0.20, 0.10],
    ).astype(float)

    # Ambient temperature: global range –15°C to 45°C
    # Weighted toward temperate regions
    ambient_temp_c = np.random.normal(loc=20, scale=15, size=n).clip(-15, 45)

    # Battery temperature: slightly higher than ambient due to charging
    temp_rise = np.random.uniform(2, 12, n)   # charging heat rise
    battery_temp_c = (ambient_temp_c + temp_rise).clip(-15, 60)

    # Charge rate (kW): Level 1 (1.4–3.3), Level 2 (7–22), DC fast (50–150)
    charger_type = np.random.choice(
        ["L1", "L2", "DC"],
        n,
        p=[0.10, 0.60, 0.30],
    )
    charge_rate_kw = np.where(
        charger_type == "L1",
        np.random.uniform(1.4, 3.3, n),
        np.where(
            charger_type == "L2",
            np.random.uniform(7, 22, n),
            np.random.uniform(50, 150, n),
        ),
    )

    # Charge cycles: new (0) to degraded (1200)
    cycle_count = np.random.exponential(scale=250, size=n).clip(0, 1200).astype(int)

    # Battery State of Health: decreases with cycles
    # Fresh: ~100%, degraded: ~70-80%
    battery_health_soh = (100 - cycle_count * 0.020 + np.random.normal(0, 2, n)).clip(70, 100)

    # --------------------------------------------------------
    # DERIVED FEATURES
    # --------------------------------------------------------
    c_rate = charge_rate_kw / battery_capacity_kwh
    soc_delta = target_soc_pct - battery_soc_pct

    # --------------------------------------------------------
    # WEAR SCORE CALCULATION (ground truth)
    # physics-informed formula with noise
    # --------------------------------------------------------

    # 1. Temperature stress (0–40 pts)
    temp_score = _temperature_score(battery_temp_c)

    # 2. High SoC stress (0–35 pts)
    soc_score = _soc_score(target_soc_pct)

    # 3. C-rate / fast charging stress (0–25 pts)
    crate_score = _crate_score(c_rate)

    # 4. Cycle aging factor — older batteries wear faster (0–10 pts bonus)
    cycle_factor = (cycle_count / 1200) * 10.0

    # Combine scores
    raw_score = temp_score + soc_score + crate_score + cycle_factor

    # Add realistic measurement noise
    noise = np.random.normal(0, 1.5, n)
    wear_score = np.clip(raw_score + noise, 0, 100).round(1)

    # --------------------------------------------------------
    # ASSEMBLE DATAFRAME
    # --------------------------------------------------------
    df = pd.DataFrame({
        "battery_soc_pct":       battery_soc_pct.round(1),
        "target_soc_pct":        target_soc_pct.round(1),
        "ambient_temp_c":        ambient_temp_c.round(1),
        "battery_temp_c":        battery_temp_c.round(1),
        "charge_rate_kw":        charge_rate_kw.round(2),
        "battery_capacity_kwh":  battery_capacity_kwh,
        "cycle_count":           cycle_count,
        "battery_health_soh":    battery_health_soh.round(1),
        "c_rate":                c_rate.round(4),
        "soc_delta":             soc_delta.round(1),
        "wear_score":            wear_score,
    })

    return df


# --------------------------------------------------------
# SCORING HELPERS (mirrors battery_degradation.py logic
# but vectorised with numpy)
# --------------------------------------------------------

def _temperature_score(temp: np.ndarray) -> np.ndarray:
    """Vectorised Arrhenius temperature penalty."""
    score = np.zeros(len(temp))

    # Optimal zone 15–25°C → 0 points
    hot_mask = temp > 25
    cold_mask = (temp >= 0) & (temp < 15)
    very_cold_mask = temp < 0

    # Heat: doubles every 10°C above 25
    excess = np.where(hot_mask, temp - 25, 0)
    score = np.where(hot_mask,
                     np.minimum(40.0, (2 ** (excess / 10) - 1) * 10),
                     score)

    # Mild cold
    deficit = np.where(cold_mask, 15 - temp, 0)
    score = np.where(cold_mask, np.minimum(25.0, deficit * 1.0), score)

    # Severe cold
    deficit_vc = np.where(very_cold_mask, 15 - temp, 0)
    score = np.where(very_cold_mask,
                     np.minimum(40.0, 15 + deficit_vc * 1.5),
                     score)
    return score


def _soc_score(target_soc: np.ndarray) -> np.ndarray:
    """Vectorised SEI growth penalty for high SoC."""
    soc_frac = target_soc / 100.0
    score = np.zeros(len(soc_frac))

    mid_mask = (soc_frac > 0.80) & (soc_frac <= 0.90)
    high_mask = soc_frac > 0.90

    score = np.where(mid_mask, ((soc_frac - 0.80) / 0.10) * 15, score)
    score = np.where(high_mask, 15 + ((soc_frac - 0.90) / 0.10) * 20, score)
    return score


def _crate_score(c_rate: np.ndarray) -> np.ndarray:
    """Vectorised C-rate mechanical stress penalty."""
    score = np.zeros(len(c_rate))

    mid_mask = (c_rate > 0.5) & (c_rate <= 1.0)
    high_mask = c_rate > 1.0

    score = np.where(mid_mask, ((c_rate - 0.5) / 0.5) * 10, score)
    score = np.where(high_mask, 10 + np.minimum(15.0, (c_rate - 1.0) * 15), score)
    return score


# --------------------------------------------------------
# MAIN
# --------------------------------------------------------

if __name__ == "__main__":
    print("[*] Generating synthetic battery degradation dataset...")
    df = generate_dataset(N_SAMPLES)

    df.to_csv(OUTPUT_FILE, index=False)

    print(f"[OK] Saved {len(df):,} rows to {OUTPUT_FILE}")
    print("\n[INFO] Dataset Summary:")
    print(df.describe().round(2))
    print(f"\n[INFO] Wear score distribution:")
    print(df["wear_score"].describe().round(2))
