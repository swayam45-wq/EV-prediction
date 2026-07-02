# ⚡ VoltWise — AI-Powered Smart EV Charging Optimizer

> **Charge smarter. Spend less. Protect your battery.**

A full-stack intelligent EV charging platform that combines **Linear Programming optimization**, **XGBoost machine learning**, and **real vehicle API integration** — built to feel like a production automotive software product.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-6.0-3178C6?logo=typescript&logoColor=white)](https://typescriptlang.org)
[![XGBoost](https://img.shields.io/badge/XGBoost-R²%3D0.993-FF6600)](https://xgboost.readthedocs.io)
[![Tests](https://img.shields.io/badge/Tests-62%20passing-brightgreen)](#-testing)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 📸 Screenshots

### Dashboard
<!-- Add your Dashboard screenshot below -->
<!-- To add: drag your screenshot into this folder and replace the placeholder -->
> 📷 <img width="959" height="494" alt="image" src="https://github.com/user-attachments/assets/d0c37107-131c-4769-9135-ee9dfc05190a" />

---

### Schedule Optimizer
<!-- Add your Optimizer page screenshot below -->
> 📷 <img width="959" height="492" alt="image" src="https://github.com/user-attachments/assets/36eb010d-d194-4281-9eec-b7f04deca7fe" />

> 
---

### Analytics & Charging History
<!-- Add your Analytics page screenshot below -->
> 📷 <img width="955" height="597" alt="image" src="https://github.com/user-attachments/assets/9624ea43-1d85-4ca0-ac45-329b74f3cef4" />

---


## 🧠 How It Works

```
User enters ZIP code → Auto-detects electricity pricing region
         ↓
Connect real EV via Smartcar / Tesla OAuth (or use Demo mode)
         ↓
Vehicle data auto-fills the form (battery %, capacity, SoH)
         ↓
 ┌─────────────────────────────────────┐
 │   FastAPI POST /api/recommend       │
 │                                     │
 │  LP Optimizer (PuLP + CBC solver)   │
 │  → Finds cheapest charging window   │
 │  → Respects departure time &        │
 │    charge rate constraints          │
 │                                     │
 │  XGBoost ML Model (R² = 0.993)      │
 │  → Predicts battery wear score      │
 │  → Trained on 15,000 sessions       │
 └─────────────────────────────────────┘
         ↓
 SQLite (SQLAlchemy async) persists session
         ↓
 React Dashboard renders:
 → Charging schedule chart
 → Cost savings breakdown
 → Wear score ring
 → AI explanations
```

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🔋 **LP Charging Optimizer** | Linear Programming finds the cheapest valid 24-hour charging schedule |
| 🤖 **XGBoost Wear Predictor** | ML model (R²=0.993) predicts battery degradation before you charge |
| 🚗 **Real EV Integration** | Connects to actual cars via Smartcar OAuth (30+ brands) & Tesla Fleet API |
| ⚡ **Live Electricity Pricing** | Real-time spot prices via Awattar API (EU) and EIA API (US) |
| 📍 **ZIP Code Region Detection** | Auto-detects your electricity pricing region from your postal code |
| 📊 **Analytics Dashboard** | Tracks savings, session history, and charging patterns over time |
| 🏥 **Battery Health Monitor** | SoH gauge, wear history, and personalized charging tips |
| 🌤️ **Weather Integration** | Adjusts recommendations based on live temperature and conditions |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+

### Backend

```bash
cd backend

# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Train the ML model (first time only, ~30 seconds)
python ml/generate_dataset.py
python ml/train.py

# 3. Apply database migrations
python -m alembic upgrade head

# 4. Start the API server
python -m uvicorn main:app --reload --port 8000
```

- **Swagger API Docs**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/health

### Frontend

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

> ⚠️ Both must run simultaneously. Vite proxies all `/api/*` requests → `localhost:8000`.

### (Optional) Connect a Real EV

Create a free account at [developer.smartcar.com](https://developer.smartcar.com), then add to `backend/.env`:

```env
SMARTCAR_CLIENT_ID=your_client_id_here
SMARTCAR_CLIENT_SECRET=your_client_secret_here
```

Restart the backend, then click **"Connect your car"** in the dashboard.

---

## 🗄️ API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/recommend` | Run LP optimizer + ML wear prediction |
| `GET` | `/api/battery-health` | SoH, wear history, and tips |
| `GET` | `/api/analytics` | Session trends, savings, and patterns |
| `GET` | `/api/prices` | 24-hour electricity price schedule |
| `GET` | `/api/prices/region-from-zip` | Map ZIP / postal code → pricing region |
| `GET` | `/api/weather` | Live weather data |
| `GET` | `/api/vehicle/status` | Real-time vehicle battery & charge state |
| `GET` | `/api/vehicle/connect` | Start Smartcar OAuth flow |
| `DELETE` | `/api/vehicle/disconnect` | Disconnect vehicle, revert to demo |
| `GET` | `/api/vehicle/providers` | List supported vehicle providers |

---

## 📊 ML Model Performance

Trained on **15,000 physics-informed synthetic charging sessions**:

| Model | RMSE | MAE | R² |
|-------|------|-----|----|
| Ridge Regression | 14.70 | 11.05 | 0.573 |
| Random Forest | 2.07 | 1.60 | 0.991 |
| **XGBoost ✅** | **1.86** | **1.42** | **0.993** |

**Top predictive features**: Target SoC (44%) · Battery temperature (22%) · C-rate (12%) · Ambient temperature (8%)

---

## 🧪 Testing

```bash
cd backend
python -m pytest tests/ -v
# Result: 62 passed, 0 failed ✅
```

**Test coverage spans:**
- API endpoint integration tests
- LP optimizer unit tests
- XGBoost inference tests
- Database CRUD tests
- Vehicle OAuth flow tests
- Heuristic degradation model tests

---

## 📁 Project Structure

```
EV-predict/
├── backend/
│   ├── api/routes/
│   │   ├── recommend.py        # POST /api/recommend — LP optimizer + ML
│   │   ├── prices.py           # GET  /api/prices — live electricity pricing
│   │   ├── vehicle.py          # GET  /api/vehicle/* — Smartcar & Tesla OAuth
│   │   ├── battery_health.py   # GET  /api/battery-health
│   │   ├── weather.py          # GET  /api/weather
│   │   └── analytics.py        # GET  /api/analytics
│   ├── services/
│   │   ├── optimizer.py        # PuLP linear programming solver
│   │   ├── pricing.py          # EIA + Awattar live pricing + TOU profiles
│   │   ├── vehicle.py          # Smartcar + Tesla + Demo vehicle service
│   │   ├── battery_degradation.py
│   │   └── recommendation.py   # Orchestration layer
│   ├── ml/
│   │   ├── generate_dataset.py # 15,000 synthetic training samples
│   │   ├── train.py            # XGBoost training pipeline
│   │   └── predict.py          # Inference with heuristic fallback
│   ├── models/                 # Pydantic schemas + SQLAlchemy ORM
│   ├── tests/                  # 62 passing tests
│   ├── config.py               # Pydantic settings
│   └── main.py                 # FastAPI app entry point
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.tsx        # Dashboard — live SoC gauge + stats
│   │   │   ├── Optimizer.tsx   # Charging form + ZIP detect + schedule chart
│   │   │   ├── BatteryHealth.tsx
│   │   │   └── Analytics.tsx   # 4-chart analytics dashboard
│   │   ├── api.ts              # Typed Axios client
│   │   ├── types.ts            # TypeScript interfaces
│   │   └── index.css           # Automotive dark design system
│   └── vite.config.ts
├── docs/                       # Detailed documentation (8 files)
└── README.md
```

---

## 🎨 Design System

Automotive-grade dark UI inspired by Tesla, Rivian, and BMW ConnectedDrive:

- **Color**: Single accent `#0ea5e9` electric blue on deep `#0d0f14` base
- **Typography**: Inter for UI + JetBrains Mono for all numeric readouts
- **Components**: Flat cards, precise 1px borders, purposeful color use
- **Charts**: Chart.js with consistent dark styling and dual Y-axis

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, TypeScript, Vite, Chart.js |
| **Backend** | Python 3.11, FastAPI, Pydantic v2 |
| **ML** | XGBoost, scikit-learn, NumPy |
| **Optimization** | PuLP + CBC solver (Linear Programming) |
| **Database** | SQLite, SQLAlchemy async, Alembic |
| **Vehicle APIs** | Smartcar OAuth, Tesla Fleet API |
| **Pricing APIs** | Awattar (EU live), EIA (US live) |
| **Testing** | pytest, pytest-asyncio, httpx |

---

## 📚 Documentation

See the [`docs/`](./docs/) folder for deep-dives into each component:

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

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with ⚡ by <a href="https://github.com/swayam45-wq">Swayam</a>
</p>
