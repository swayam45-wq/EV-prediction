# AI-Powered Smart EV Charging Recommendation System

An intelligent EV charging optimization platform that minimizes charging cost while maximizing battery health and ensuring the vehicle is ready before departure.

## 🚀 Features

- **LP-Based Charging Optimizer** — Uses Linear Programming (PuLP/CBC) to find the cheapest hourly charging schedule
- **Battery Degradation Scoring** — Heuristic model accounting for temperature, SoC stress, and C-rate
- **Cost Savings Analysis** — Compares naive (immediate) charging vs. optimized schedule
- **Weather-Aware Adjustments** — Penalizes charging during extreme temperatures
- **AI Recommendation Engine** — Generates human-readable explanations for every scheduling decision

## 📁 Project Structure

```
EV-predict/
├── backend/
│   ├── main.py                   # FastAPI app entrypoint
│   ├── config.py                 # App settings
│   ├── api/routes/               # API endpoints
│   ├── models/schemas.py         # Pydantic request/response models
│   ├── services/                 # Business logic layer
│   │   ├── optimizer.py          # LP charging optimizer
│   │   ├── battery_degradation.py
│   │   ├── cost_analyzer.py
│   │   ├── recommendation_engine.py
│   │   └── weather.py
│   ├── ml/                       # ML model training & inference
│   └── tests/                    # Automated tests
├── frontend/                     # React app (Phase 2)
├── requirements.txt
└── README.md
```

## ⚡ Quick Start

### Prerequisites
- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/swayam45-wq/EV-prediction.git
cd EV-predict

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Run the Server

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### Test the API

```bash
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "current_soc": 35,
    "target_soc": 80,
    "battery_capacity_kwh": 75,
    "max_charge_rate_kw": 11,
    "battery_health_soh": 92,
    "departure_time": "08:00",
    "temperature_celsius": 28,
    "weather_condition": "clear",
    "electricity_prices": [
      {"hour": "00:00", "price": 0.12},
      {"hour": "01:00", "price": 0.10},
      {"hour": "02:00", "price": 0.08},
      {"hour": "03:00", "price": 0.07},
      {"hour": "04:00", "price": 0.08},
      {"hour": "05:00", "price": 0.10},
      {"hour": "06:00", "price": 0.15},
      {"hour": "07:00", "price": 0.22}
    }
  }'
```

### Run Tests

```bash
cd backend
python -m pytest tests/ -v
```

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/recommend` | Get optimal charging recommendation |
| GET | `/api/battery-health` | Get battery health analysis |
| GET | `/api/analytics` | Get charging analytics |
| GET | `/health` | Health check |
| GET | `/docs` | Interactive API documentation (Swagger) |

## 🧠 How the Optimizer Works

The system formulates EV charging as a **Linear Programming** problem:

- **Decision Variables**: Energy charged (kWh) in each hourly time slot
- **Objective**: Minimize `Σ(price[t] × energy[t])` + degradation penalty
- **Constraints**: Target charge reached, departure deadline, max charging rate

## 🔧 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, Python 3.10+ |
| Optimization | PuLP (CBC solver) |
| ML (planned) | Scikit-Learn, XGBoost |
| Frontend (Phase 2) | React, TypeScript, Tailwind CSS, Chart.js |
| Database (Phase 2) | PostgreSQL, Redis |

## 📜 License

MIT
