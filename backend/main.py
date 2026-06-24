"""
FastAPI Application Entrypoint.

AI-Powered Smart EV Charging Recommendation System.

Run locally with:
    uvicorn main:app --reload --port 8000

Interactive docs at:
    http://localhost:8000/docs
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from models.database import init_db
from api.routes.recommend import router as recommend_router
from api.routes.battery_health import router as battery_health_router
from api.routes.analytics import router as analytics_router
from api.routes.weather import router as weather_router
from api.routes.prices import router as prices_router

logger = logging.getLogger(__name__)


# ============================================================
# LIFESPAN — startup / shutdown
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise DB tables and load ML model on startup."""
    logger.info("Starting up — initialising database...")
    await init_db()
    logger.info("Database ready.")

    # Warm-up: load ML model into memory so first request is fast
    from ml.predict import _load_artifacts
    loaded = _load_artifacts()
    logger.info("ML model loaded: %s", loaded)

    yield  # App runs here

    logger.info("Shutting down.")



# ============================================================
# APP INITIALIZATION
# ============================================================

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    description=(
        "AI-Powered Smart EV Charging Recommendation System. "
        "Combines Linear Programming (PuLP/CBC), XGBoost ML, live weather data, "
        "dynamic electricity pricing, and V2G support to compute optimal "
        "hourly charging schedules that minimize cost and protect battery health."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)


# ============================================================
# MIDDLEWARE
# ============================================================

# CORS — allow frontend to communicate with the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # React dev server
        "http://localhost:5173",   # Vite dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROUTE REGISTRATION
# ============================================================

app.include_router(recommend_router)
app.include_router(battery_health_router)
app.include_router(analytics_router)
app.include_router(weather_router)
app.include_router(prices_router)


# ============================================================
# ROOT & HEALTH ENDPOINTS
# ============================================================

@app.get("/", tags=["Root"])
async def root():
    """API welcome message with available endpoints."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "recommend":      "POST /api/recommend",
            "battery_health": "GET  /api/battery-health",
            "analytics":      "GET  /api/analytics",
            "weather":        "GET  /api/weather?city=Mumbai",
            "prices":         "GET  /api/prices?region=US_CA",
            "health":         "GET  /health",
        },
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Simple health check for monitoring and load balancers."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.app_env,
    }
