# AI-Powered Smart EV Charging Recommendation System

> **Minimize cost · Protect battery health · Be ready on time**

A full-stack intelligent EV charging platform combining **Linear Programming optimization**, **XGBoost machine learning**, and a **professional React dashboard** — built to feel like a real automotive software product.

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-6.0-blue?logo=typescript)](https://typescriptlang.org)
[![XGBoost](https://img.shields.io/badge/XGBoost-R²=0.993-orange)](https://xgboost.readthedocs.io)
[![Tests](https://img.shields.io/badge/Tests-55%20passing-brightgreen)](#testing)

---

## 🚀 Feature Status

| Feature | Tech | Phase | Status |
|---------|------|-------|--------|
| LP Charging Optimizer | PuLP + CBC solver | 1 | ✅ Done |
| Battery Degradation Heuristic | Custom formula | 1 | ✅ Done |
| REST API (5 endpoints) | FastAPI + Pydantic | 1 | ✅ Done |
| XGBoost Wear Prediction | scikit-learn + XGBoost | 2 | ✅ Done |
| Async SQLite Database | SQLAlchemy + aiosqlite | 2 | ✅ Done |
| DB Migrations | Alembic | 2 | ✅ Done |
| Full Test Suite (55 tests) | pytest + pytest-asyncio | 2 | ✅ Done |
| React Dashboard (4 pages) | Vite + TypeScript + Tailwind | 3 | ✅ Done |
| Automotive UI Redesign | Custom CSS design system | 3 | ✅ Done |
| Live Weather API | OpenWeatherMap | 4 | 🔜 Planned |
| Real-time Electricity Pricing | EIA / ENTSOE API | 4 | 🔜 Planned |
| LLM-powered Explanations | OpenAI GPT-4 | 4 | 🔜 Planned |
| V2G (Vehicle-to-Grid) Support | Custom | 4 | 🔜 Planned |

---

## ⚡ Quick Start

### Backend

```bash
cd backend

# 1. Install dependencies
pip install -r requirements.txt

# 2. Train the ML model (first time only, ~30s)
python ml/generate_dataset.py
python ml/train.py

# 3. Apply database migrations
python -m alembic upgrade head

# 4. Start the API server
python -m uvicorn main:app --reload --port 8000
```

- **API docs (Swagger)**: http://localhost:8000/docs  
- **Health check**: http://localhost:8000/health

### Frontend

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

> Both must run simultaneously. The Vite proxy routes `/api/*` → `localhost:8000`.

---

## 📁 Project Structure

```
EV-predict/
├── backend/
│   ├── api/
│   │   └── routes/
│   │       ├── recommend.py      # POST /api/recommend — LP optimizer + ML
│   │       ├── battery_health.py # GET  /api/battery-health
│   │       └── analytics.py      # GET  /api/analytics
│   ├── services/
│   │   ├── optimizer.py          # PuLP linear programming solver
│   │   ├── battery_degradation.py# Heuristic wear model (fallback)
│   │   ├── cost_analyzer.py      # Cost comparison logic
│   │   └── recommendation.py     # Orchestration layer
│   ├── ml/
│   │   ├── generate_dataset.py   # 15,000 synthetic training samples
│   │   ├── train.py              # XGBoost training pipeline
│   │   ├── predict.py            # Inference with graceful heuristic fallback
│   │   └── models/               # Saved artifacts (gitignored)
│   ├── models/
│   │   ├── schemas.py            # Pydantic request/response models
│   │   └── database.py           # SQLAlchemy async ORM models
│   ├── alembic/                  # DB migration scripts
│   ├── tests/                    # 55 passing tests
│   │   ├── conftest.py           # In-memory SQLite fixtures
│   │   ├── test_api.py           # Endpoint integration tests
│   │   ├── test_optimizer.py     # LP solver unit tests
│   │   ├── test_degradation.py   # Heuristic model tests
│   │   ├── test_ml_predict.py    # XGBoost inference tests
│   │   └── test_database.py      # DB CRUD + endpoint tests
│   ├── main.py                   # FastAPI app + lifespan DB init
│   ├── config.py                 # Pydantic settings (v2.0.0)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── index.css             # Automotive dark design system
│   │   ├── App.tsx               # Root + sidebar layout + routes
│   │   ├── api.ts                # Typed Axios client
│   │   ├── types.ts              # TypeScript interfaces
│   │   ├── components/
│   │   │   └── Navbar.tsx        # Sidebar nav with vehicle status card
│   │   └── pages/
│   │       ├── Home.tsx          # Dashboard — SoC gauge + stats
│   │       ├── Optimizer.tsx     # Charging form + schedule chart
│   │       ├── BatteryHealth.tsx # SoH gauge + wear history
│   │       └── Analytics.tsx     # 4-chart analytics dashboard
│   ├── vite.config.ts            # Vite + Tailwind v4 + API proxy
│   └── package.json
├── docs/                         # 8 detailed documentation files
└── README.md
```

---

## 🧠 How It Works

```
User Input (SoC, departure, capacity, prices)
        ↓
[FastAPI POST /api/recommend]
        ↓
 LP Optimizer (PuLP + CBC)
 → Finds minimum-cost hourly schedule
 → Constraints: energy target, charge rate, departure time
        ↓
 XGBoost ML Model
 → Predicts wear score (0–100) from temperature, C-rate, target SoC
 → Falls back to heuristic if model not available
        ↓
 SQLite DB (SQLAlchemy async)
 → Persists every session for analytics
        ↓
 JSON Response
 → Schedule, cost savings, wear score, AI explanations
        ↓
 React Dashboard
 → Schedule chart, cost breakdown, wear ring, trend charts
```

---

## 📊 ML Model Performance

Trained on 15,000 physics-informed synthetic charging sessions:

| Model | RMSE | MAE | R² |
|-------|------|-----|----|
| Ridge Regression | 14.70 | 11.05 | 0.573 |
| Random Forest | 2.07 | 1.60 | 0.991 |
| **XGBoost** ✅ | **1.86** | **1.42** | **0.993** |

**Top features**: target SoC (44%), battery temp (22%), C-rate (12%), ambient temp (8%)

---

## 🗄️ API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | App info + version |
| `GET` | `/health` | Health check |
| `POST` | `/api/recommend` | Optimize charging schedule |
| `GET` | `/api/battery-health` | SoH, wear history, tips |
| `GET` | `/api/analytics` | Session trends, savings, patterns |

---

## 🧪 Testing

```bash
cd backend
python -m pytest tests/ -v
# Result: 55 passed, 0 failed
```

Coverage: API endpoints, LP optimizer, heuristic model, XGBoost inference, DB CRUD, analytics endpoints.

---

## 🎨 Frontend Design

Automotive-grade dark UI inspired by Tesla, Rivian, BMW ConnectedDrive:

- **Sidebar navigation** with live vehicle status card
- **Single accent color** (#0ea5e9 electric blue)
- **JetBrains Mono** for all numeric readouts (tabular numbers)
- **No gradient soup** — flat cards, precise borders, purposeful color use
- **Professional data tables** for session logs and cost breakdowns
- **Chart.js** visualizations with consistent dark styling

---

## 📚 Documentation

See the [`docs/`](./docs/) folder:

| File | Contents |
|------|----------|
| `01_project_overview.md` | Goals, problem statement, architecture |
| `02_architecture.md` | System design, data flow diagram |
| `03_optimizer.md` | LP formulation, constraints, solver config |
| `04_degradation_model.md` | Heuristic wear scoring formula |
| `04b_ml_model_phase2.md` | XGBoost pipeline, metrics, feature importance |
| `05_api_reference.md` | All endpoints with request/response examples |
| `05b_setup_guide.md` | Installation, environment setup, troubleshooting |
| `06_frontend_phase3.md` | React dashboard guide, design system, pages |
