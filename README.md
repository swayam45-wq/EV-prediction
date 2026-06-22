# AI-Powered Smart EV Charging Recommendation System

> **Minimize cost · Protect battery health · Be ready on time**

A full-stack intelligent EV charging platform that combines **Linear Programming optimization**, **XGBoost machine learning**, and a **React dashboard** to give EV owners the perfect charging schedule.

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-6.0-blue?logo=typescript)](https://typescriptlang.org)
[![XGBoost](https://img.shields.io/badge/XGBoost-R²=0.99-orange)](https://xgboost.readthedocs.io)

---

## 🚀 Live Features

| Feature | Tech | Status |
|---------|------|--------|
| LP Charging Optimizer | PuLP + CBC | ✅ Phase 1 |
| Battery Degradation (Heuristic) | Custom formula | ✅ Phase 1 |
| XGBoost Wear Prediction | scikit-learn + XGBoost | ✅ Phase 2 |
| Session Database | SQLAlchemy + SQLite | ✅ Phase 2 |
| DB Migrations | Alembic | ✅ Phase 2 |
| React Dashboard | Vite + Tailwind + Chart.js | ✅ Phase 3 |
| Live Weather API | OpenWeatherMap | 🔜 Phase 4 |
| Real-time Pricing | EIA / ENTSOE API | 🔜 Phase 4 |
| LLM Explanations | OpenAI GPT-4 | 🔜 Phase 4 |
| V2G (Vehicle-to-Grid) | Custom | 🔜 Phase 4 |

---

## 🛠️ Quick Start

### Backend (FastAPI)

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Train the ML model (first time only, ~30s)
python ml/generate_dataset.py
python ml/train.py

# Apply database migrations
python -m alembic upgrade head

# Start the server
uvicorn main:app --reload --port 8000
```

API docs at: http://localhost:8000/docs

### Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

Dashboard at: http://localhost:5173

---

## 📁 Project Structure

```
EV-predict/
├── backend/
│   ├── api/routes/           # FastAPI route handlers
│   ├── services/             # LP optimizer, cost analyzer, weather, recommendations
│   ├── ml/
│   │   ├── generate_dataset.py   # Synthetic training data
│   │   ├── train.py              # XGBoost training pipeline
│   │   ├── predict.py            # ML inference (with heuristic fallback)
│   │   └── models/               # Saved model artifacts (gitignored)
│   ├── models/
│   │   ├── schemas.py            # Pydantic request/response models
│   │   └── database.py           # SQLAlchemy async models
│   ├── alembic/                  # Database migrations
│   ├── tests/                    # 55 passing tests
│   ├── main.py                   # FastAPI app entrypoint
│   └── config.py                 # Settings management
├── frontend/
│   ├── src/
│   │   ├── pages/            # Home, Optimizer, BatteryHealth, Analytics
│   │   ├── components/       # Navbar
│   │   ├── api.ts            # Typed Axios client
│   │   └── types.ts          # TypeScript interfaces
│   └── vite.config.ts
├── docs/                     # Detailed documentation (9 files)
└── README.md
```

---

## 🧠 How the Optimizer Works

1. **Input**: Current SoC, target SoC, departure time, 24h electricity prices, battery specs
2. **LP Solve**: PuLP + CBC finds minimum-cost hourly schedule satisfying all constraints
3. **ML Wear Score**: XGBoost predicts battery degradation (R²=0.9932, trained on 15k samples)
4. **DB Persist**: Every session saved to SQLite for analytics
5. **Output**: Optimal start/stop times, schedule chart, cost savings, health advice

---

## 📊 ML Model Performance

| Model | RMSE | R² |
|-------|------|-----|
| Ridge Regression | 14.7 | 0.573 |
| Random Forest | 2.07 | 0.991 |
| **XGBoost ✅** | **1.86** | **0.993** |

Top features: target SoC (44%), battery temp (22%), C-rate (12%)

---

## 🧪 Tests

```bash
cd backend
python -m pytest tests/ -v
# 55 tests, 0 failures
```

---

## 📚 Documentation

See [`docs/`](./docs/) for detailed guides:

- `01_project_overview.md` — Goals, architecture, problem statement
- `02_architecture.md` — System design, data flow
- `03_optimizer.md` — LP formulation, constraints
- `04_degradation_model.md` — Heuristic wear model
- `04b_ml_model_phase2.md` — XGBoost pipeline, metrics
- `05_api_reference.md` — All endpoints with examples
- `05b_setup_guide.md` — Installation and deployment
- `06_frontend_phase3.md` — React dashboard guide
- `07_roadmap.md` — Phase 4 and beyond
