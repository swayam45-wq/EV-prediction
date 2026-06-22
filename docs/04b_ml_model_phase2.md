# 04b. ML Battery Degradation Model (Phase 2)

## Overview

In Phase 2, the rule-based heuristic from `battery_degradation.py` is replaced by a **trained XGBoost machine learning model** (`ml/predict.py`). The heuristic is retained as a graceful fallback.

## Training Pipeline

### Step 1 — Dataset Generation (`ml/generate_dataset.py`)
Generates **15,000 synthetic charging sessions** using physics-informed formulas:

| Feature | Distribution | Range |
|---------|-------------|-------|
| `battery_soc_pct` | Uniform | 10–90% |
| `target_soc_pct` | Derived | 10–100% |
| `ambient_temp_c` | Normal (µ=20, σ=15) | –15–45°C |
| `battery_temp_c` | ambient + rise | –15–60°C |
| `charge_rate_kw` | Mixed (L1/L2/DC) | 1.4–150 kW |
| `battery_capacity_kwh` | Categorical | 40/58/64/75/82/100 kWh |
| `cycle_count` | Exponential | 0–1200 |
| `battery_health_soh` | Derived from cycles | 70–100% |
| `c_rate` | Derived | charge_rate/capacity |
| `soc_delta` | Derived | target – current SoC |

### Step 2 — Model Training (`ml/train.py`)
Trains and evaluates three models:

| Model | RMSE | MAE | R² |
|-------|------|-----|----|
| Ridge Regression | 14.702 | 11.051 | 0.5734 |
| Random Forest | 2.074 | 1.603 | 0.9915 |
| **XGBoost** ✅ | **1.857** | **1.417** | **0.9932** |

XGBoost is saved as the production model artifact.

### Top Feature Importances (XGBoost)
```
target_soc_pct        ||||||||||||||||||||||||  (44.4%)
battery_temp_c        ||||||||||              (21.7%)
c_rate                ||||||                  (12.2%)
ambient_temp_c        ||||                    (8.0%)
battery_soc_pct       |||                     (7.2%)
```

## How to Re-train

```bash
cd backend

# Generate fresh dataset (optional, ~15s)
python ml/generate_dataset.py

# Train all models and save artifacts (~30s)
python ml/train.py
```

## Inference (`ml/predict.py`)

The `predict_wear_score()` function:
1. Lazy-loads the model and scaler on first call (fast subsequent calls)
2. Falls back to heuristic if model files not found
3. Returns a dict with `total_score`, `rating`, `source`, and `recommendations`

## Model Artifacts

Saved to `backend/ml/models/` (gitignored):
- `wear_score_model.joblib` — trained XGBoost model
- `wear_score_scaler.joblib` — fitted StandardScaler
- `model_metadata.json` — metrics, feature list, hyperparameters

## Database Integration

Every call to `POST /api/recommend` now persists the session to SQLite:
- Input features (SoC, temp, departure time, etc.)
- Optimization results (schedule, cost savings)
- ML wear score and source (`ml_model` or `heuristic`)

This data feeds the `/api/analytics` and `/api/battery-health` dashboards.
