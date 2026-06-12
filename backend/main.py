"""
FastAPI Application Entrypoint.

AI-Powered Smart EV Charging Recommendation System.

Run locally with:
    uvicorn main:app --reload --port 8000

Interactive docs at:
    http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from api.routes.recommend import router as recommend_router
from api.routes.battery_health import router as battery_health_router
from api.routes.analytics import router as analytics_router


# ============================================================
# APP INITIALIZATION
# ============================================================

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "An intelligent EV charging optimization platform that minimizes "
        "charging cost while maximizing battery health and ensuring the "
        "vehicle is ready before departure. Uses Linear Programming (PuLP) "
        "to compute optimal hourly charging schedules."
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
            "recommend": "POST /api/recommend",
            "battery_health": "GET /api/battery-health",
            "analytics": "GET /api/analytics",
            "health": "GET /health",
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
