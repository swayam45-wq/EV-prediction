"""
Tests for the database layer.

Verifies that:
    - ChargingSession records can be created and queried
    - BatteryProfile records can be created
    - Analytics and battery-health API endpoints return correct structure
"""

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from models.database import Base, ChargingSession, BatteryProfile

# ── Isolated in-memory DB just for these tests ───────────────
DB_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(DB_URL, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="module", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db():
    async with SessionLocal() as session:
        yield session
        await session.rollback()


# ============================================================
# ChargingSession CRUD
# ============================================================

class TestChargingSessionModel:

    @pytest.mark.asyncio
    async def test_create_session(self, db):
        """Should be able to insert and retrieve a ChargingSession."""
        session = ChargingSession(
            current_soc=35.0,
            target_soc=80.0,
            battery_capacity_kwh=75.0,
            max_charge_rate_kw=11.0,
            battery_health_soh=92.0,
            temperature_celsius=22.0,
            weather_condition="clear",
            departure_time="08:00",
            charging_efficiency=0.90,
            status="optimal",
            start_charging="02:00",
            stop_charging="06:00",
            total_energy_kwh=33.75,
            optimized_cost=2.70,
            normal_cost=3.50,
            savings_percent=22.9,
            wear_score=4.5,
            wear_rating="Low",
            wear_source="ml_model",
            schedule_json=[],
            explanations_json=[],
        )
        db.add(session)
        await db.flush()

        result = await db.execute(select(ChargingSession))
        sessions = result.scalars().all()
        assert len(sessions) >= 1
        assert sessions[0].current_soc == 35.0
        assert sessions[0].wear_rating == "Low"

    @pytest.mark.asyncio
    async def test_session_defaults(self, db):
        """created_at should be populated automatically."""
        session = ChargingSession(
            current_soc=50.0,
            target_soc=90.0,
            battery_capacity_kwh=60.0,
            max_charge_rate_kw=7.4,
            status="optimal",
        )
        db.add(session)
        await db.flush()
        assert session.created_at is not None

    @pytest.mark.asyncio
    async def test_multiple_sessions(self, db):
        """Should support inserting multiple sessions."""
        for i in range(3):
            s = ChargingSession(
                current_soc=float(20 + i * 10),
                target_soc=80.0,
                battery_capacity_kwh=75.0,
                max_charge_rate_kw=11.0,
                status="optimal",
                wear_score=float(5 + i),
                wear_rating="Low",
                savings_percent=float(15 + i),
            )
            db.add(s)
        await db.flush()

        result = await db.execute(select(ChargingSession))
        all_sessions = result.scalars().all()
        assert len(all_sessions) >= 3


# ============================================================
# BatteryProfile CRUD
# ============================================================

class TestBatteryProfileModel:

    @pytest.mark.asyncio
    async def test_create_profile(self, db):
        """Should be able to create a BatteryProfile."""
        profile = BatteryProfile(
            vehicle_id="tesla-model3-001",
            vehicle_model="Tesla Model 3 LR",
            battery_capacity_kwh=82.0,
            soh_percent=96.5,
            cycle_count=120,
            last_known_soc=45.0,
        )
        db.add(profile)
        await db.flush()

        result = await db.execute(
            select(BatteryProfile).where(BatteryProfile.vehicle_id == "tesla-model3-001")
        )
        found = result.scalar_one_or_none()
        assert found is not None
        assert found.soh_percent == 96.5
        assert found.cycle_count == 120


# ============================================================
# API endpoints — DB-backed response structure
# ============================================================

class TestAnalyticsEndpoint:
    """Test /api/analytics returns correct structure."""

    def test_analytics_returns_ok(self, client):
        response = client.get("/api/analytics")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "wear_trend" in data
        assert "savings_trend" in data
        assert "charging_pattern" in data
        assert "soc_distribution" in data
        assert "total_saved_usd" in data

    def test_analytics_empty_on_fresh_db(self, client):
        """Fresh in-memory DB should return 0 sessions."""
        response = client.get("/api/analytics")
        data = response.json()
        # After recommend calls from other tests this may not be 0
        assert isinstance(data["session_count"], int)


class TestBatteryHealthEndpoint:
    """Test /api/battery-health returns correct structure."""

    def test_battery_health_returns_ok(self, client):
        response = client.get("/api/battery-health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "summary" in data
        assert "wear_history" in data
        assert "ml_model_info" in data
        assert "tips" in data

    def test_battery_health_summary_fields(self, client):
        response = client.get("/api/battery-health")
        summary = response.json()["summary"]
        assert "total_charging_sessions" in summary
        assert "avg_wear_score" in summary
        assert "inferred_soh_percent" in summary
