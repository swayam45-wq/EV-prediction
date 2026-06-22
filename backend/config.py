"""
Application configuration module.

Loads settings from environment variables with sensible defaults
for local development. Uses pydantic-settings for validation.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # --- Application ---
    app_name: str = "EV Charging Optimizer"
    app_version: str = "2.0.0"
    app_env: str = "development"
    debug: bool = True

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000

    # --- Optimization Defaults ---
    default_charging_efficiency: float = 0.90  # 90% wall-to-battery efficiency
    default_temperature_celsius: float = 25.0  # Comfortable ambient temp
    max_solver_time_seconds: int = 30          # PuLP CBC timeout

    # --- Database (Phase 2) ---
    # SQLite for local dev, set DATABASE_URL for PostgreSQL in production
    database_url: Optional[str] = None
    redis_url: Optional[str] = None

    # --- ML Model (Phase 2) ---
    ml_models_dir: str = os.path.join(os.path.dirname(__file__), "ml", "models")
    ml_model_file: str = "wear_score_model.joblib"
    ml_scaler_file: str = "wear_score_scaler.joblib"

    # --- External APIs (Phase 4) ---
    openweather_api_key: Optional[str] = None
    electricity_price_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None


# Singleton instance — import this throughout the app
settings = Settings()

