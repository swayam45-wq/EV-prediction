"""
Database models using SQLAlchemy 2.0 (async).

Tables:
    - charging_sessions  : Every optimize request + its result
    - battery_profiles   : Per-vehicle battery stats over time

The DB URL defaults to SQLite for local dev.
Set DATABASE_URL in .env to switch to PostgreSQL for production.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, Float, String, Boolean,
    DateTime, JSON, Text, ForeignKey,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession, create_async_engine, async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase, relationship

from config import settings


# ── Engine + Session factory ─────────────────────────────────

def _make_engine():
    """Build async engine from config. Supports SQLite & PostgreSQL."""
    url = settings.database_url or "sqlite+aiosqlite:///./ev_charging.db"

    # SQLite-specific connect_args (allow same conn from multiple threads)
    if url.startswith("sqlite"):
        return create_async_engine(
            url,
            echo=settings.debug,
            connect_args={"check_same_thread": False},
        )
    return create_async_engine(url, echo=settings.debug)


engine = _make_engine()

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


# ── Dependency for FastAPI routes ────────────────────────────

async def get_db() -> AsyncSession:
    """FastAPI dependency that yields a DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── Table: charging_sessions ─────────────────────────────────

class ChargingSession(Base):
    """
    Stores every /api/recommend request + its optimized output.
    Used for analytics, history, and improving the ML model.
    """
    __tablename__ = "charging_sessions"

    id = Column(Integer, primary_key=True, index=True)

    # --- Vehicle inputs ---
    current_soc          = Column(Float, nullable=False)
    target_soc           = Column(Float, nullable=False)
    battery_capacity_kwh = Column(Float, nullable=False)
    max_charge_rate_kw   = Column(Float, nullable=False)
    battery_health_soh   = Column(Float, default=100.0)

    # --- Environment ---
    temperature_celsius  = Column(Float, default=25.0)
    weather_condition    = Column(String(50), default="clear")

    # --- Schedule ---
    departure_time       = Column(String(10))
    charging_efficiency  = Column(Float, default=0.90)

    # --- Results ---
    status               = Column(String(20))           # optimal / infeasible
    start_charging       = Column(String(10))           # e.g. "02:00"
    stop_charging        = Column(String(10))
    total_energy_kwh     = Column(Float)
    optimized_cost       = Column(Float)
    normal_cost          = Column(Float)
    savings_percent      = Column(Float)
    wear_score           = Column(Float)
    wear_rating          = Column(String(10))
    wear_source          = Column(String(20))           # ml_model / heuristic

    # --- Raw JSON blobs (for full replay / analytics) ---
    schedule_json        = Column(JSON)
    explanations_json    = Column(JSON)

    # --- Metadata ---
    created_at           = Column(DateTime, default=datetime.utcnow)


# ── Table: battery_profiles ──────────────────────────────────

class BatteryProfile(Base):
    """
    Tracks a vehicle's battery health over time.
    Populated by user updates or vehicle API data.
    """
    __tablename__ = "battery_profiles"

    id = Column(Integer, primary_key=True, index=True)

    vehicle_id           = Column(String(100), index=True)  # user-defined tag
    vehicle_model        = Column(String(100))
    battery_capacity_kwh = Column(Float)

    # Current snapshot
    soh_percent          = Column(Float)         # State of Health %
    cycle_count          = Column(Integer, default=0)
    last_known_soc       = Column(Float)

    # Predicted metrics (Phase 4 — will be populated by ML)
    predicted_rul_years  = Column(Float)         # Remaining Useful Life

    recorded_at          = Column(DateTime, default=datetime.utcnow)


# ── Helper: create all tables ────────────────────────────────

async def init_db():
    """Create all tables if they don't exist. Called on app startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
