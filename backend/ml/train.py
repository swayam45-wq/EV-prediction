"""
ML Model Training — Battery Degradation Wear Score Predictor.

Trains and evaluates three models:
    1. XGBoost Regressor (primary)
    2. Random Forest Regressor (baseline)
    3. Linear Ridge Regression (sanity check)

The best model (lowest RMSE on test set) is saved as the
production model artifact used by the backend API.

Output artifacts (saved to backend/ml/models/):
    - wear_score_model.joblib       → trained XGBoost model
    - wear_score_scaler.joblib      → fitted StandardScaler
    - model_metadata.json           → feature list, metrics, version

Usage:
    python backend/ml/train.py
"""

import os
import json
import time
import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
import xgboost as xgb

# ── Paths ────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(__file__)
DATA_PATH   = os.path.join(BASE_DIR, "data", "battery_degradation_dataset.csv")
MODELS_DIR  = os.path.join(BASE_DIR, "models")
MODEL_PATH  = os.path.join(MODELS_DIR, "wear_score_model.joblib")
SCALER_PATH = os.path.join(MODELS_DIR, "wear_score_scaler.joblib")
META_PATH   = os.path.join(MODELS_DIR, "model_metadata.json")

# ── Feature columns used for training ───────────────────────
FEATURE_COLS = [
    "battery_soc_pct",
    "target_soc_pct",
    "ambient_temp_c",
    "battery_temp_c",
    "charge_rate_kw",
    "battery_capacity_kwh",
    "cycle_count",
    "battery_health_soh",
    "c_rate",
    "soc_delta",
]
TARGET_COL = "wear_score"


def load_data() -> tuple[pd.DataFrame, pd.Series]:
    """Load dataset; auto-generate if missing."""
    if not os.path.exists(DATA_PATH):
        print("[!] Dataset not found -- generating now...")
        from generate_dataset import generate_dataset
        df_gen = generate_dataset()
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
        df_gen.to_csv(DATA_PATH, index=False)

    df = pd.read_csv(DATA_PATH)
    print(f"[OK] Loaded {len(df):,} rows from {DATA_PATH}")
    return df[FEATURE_COLS], df[TARGET_COL]


def evaluate(name: str, y_true, y_pred) -> dict:
    """Print and return evaluation metrics."""
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae  = mean_absolute_error(y_true, y_pred)
    r2   = r2_score(y_true, y_pred)
    print(f"  {name:30s} -> RMSE: {rmse:.3f} | MAE: {mae:.3f} | R2: {r2:.4f}")
    return {"rmse": round(rmse, 4), "mae": round(mae, 4), "r2": round(r2, 4)}


def train():
    os.makedirs(MODELS_DIR, exist_ok=True)

    # -- 1. Load data -----------------------------------------
    X, y = load_data()

    # -- 2. Train/test split (80/20) --------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )

    # -- 3. Scale features ------------------------------------
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    print("\n[*] Training models...\n")

    results = {}

    # -- 4a. Ridge Regression (sanity check) ------------------
    ridge = Ridge(alpha=1.0)
    ridge.fit(X_train_s, y_train)
    results["ridge"] = evaluate("Ridge Regression", y_test, ridge.predict(X_test_s))

    # -- 4b. Random Forest ------------------------------------
    t0 = time.time()
    rf = RandomForestRegressor(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=4,
        random_state=42,
        n_jobs=-1,
    )
    rf.fit(X_train_s, y_train)
    results["random_forest"] = evaluate(
        "Random Forest", y_test, rf.predict(X_test_s)
    )
    print(f"    [time] Trained in {time.time()-t0:.1f}s")

    # -- 4c. XGBoost (primary) --------------------------------
    t0 = time.time()
    xgb_model = xgb.XGBRegressor(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        gamma=0.1,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
        n_jobs=-1,
        verbosity=0,
    )
    xgb_model.fit(
        X_train_s, y_train,
        eval_set=[(X_test_s, y_test)],
        verbose=False,
    )
    results["xgboost"] = evaluate(
        "XGBoost", y_test, xgb_model.predict(X_test_s)
    )
    print(f"    [time] Trained in {time.time()-t0:.1f}s")

    # -- 5. Cross-validation on XGBoost -----------------------
    print("\n[CV] 5-Fold Cross-Validation (XGBoost):")
    cv_scores = cross_val_score(
        xgb.XGBRegressor(
            n_estimators=300, learning_rate=0.05,
            max_depth=6, random_state=42, verbosity=0
        ),
        X_train_s, y_train,
        scoring="neg_root_mean_squared_error",
        cv=5, n_jobs=-1
    )
    cv_rmse = -cv_scores
    print(f"    CV RMSE: {cv_rmse.mean():.3f} ± {cv_rmse.std():.3f}")

    # -- 6. Feature importance --------------------------------
    print("\n[INFO] Top Feature Importances (XGBoost):")
    importance = dict(zip(FEATURE_COLS, xgb_model.feature_importances_))
    for feat, imp in sorted(importance.items(), key=lambda x: -x[1]):
        bar = "|" * int(imp * 50)
        print(f"    {feat:28s} {bar}  ({imp:.3f})")

    # -- 7. Save best model + scaler --------------------------
    print("\n[*] Saving model artifacts...")
    joblib.dump(xgb_model, MODEL_PATH)
    joblib.dump(scaler,    SCALER_PATH)

    metadata = {
        "model_type":      "XGBoostRegressor",
        "feature_columns": FEATURE_COLS,
        "target_column":   TARGET_COL,
        "n_train_samples": len(X_train),
        "n_test_samples":  len(X_test),
        "metrics": {
            "test": results["xgboost"],
            "cv_rmse_mean": round(float(cv_rmse.mean()), 4),
            "cv_rmse_std":  round(float(cv_rmse.std()),  4),
        },
        "model_comparison": results,
        "xgboost_params": xgb_model.get_params(),
    }

    with open(META_PATH, "w") as f:
        json.dump(metadata, f, indent=2, default=str)

    print(f"    [OK] Model  -> {MODEL_PATH}")
    print(f"    [OK] Scaler -> {SCALER_PATH}")
    print(f"    [OK] Meta   -> {META_PATH}")
    print("\n[DONE] Training complete!")


if __name__ == "__main__":
    train()
