# 05b. Setup Guide

## Prerequisites

| Tool | Minimum Version | Install |
|------|----------------|---------|
| Python | 3.11+ | https://python.org |
| Node.js | 18+ | https://nodejs.org |
| Git | Any | https://git-scm.com |

---

## Backend Setup

### 1. Clone the repository
```bash
git clone https://github.com/swayam45-wq/EV-prediction.git
cd EV-prediction
```

### 2. Install Python dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Set up environment variables
```bash
# Copy the example env file
cp ../.env.example .env
# Edit .env if needed (all defaults work for local dev)
```

### 4. Train the ML model (first time only)
```bash
# Generate 15,000 synthetic training samples (~15s)
python ml/generate_dataset.py

# Train XGBoost model (~30s)
python ml/train.py
# Artifacts saved to: ml/models/wear_score_model.joblib
```

### 5. Apply database migrations
```bash
python -m alembic upgrade head
# Creates ev_charging.db in backend/
```

### 6. Start the API server
```bash
uvicorn main:app --reload --port 8000
```

API is live at:
- **Interactive docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health check**: http://localhost:8000/health

---

## Frontend Setup

### 1. Install dependencies
```bash
cd frontend
npm install
```

### 2. Start the dev server
```bash
npm run dev
# Opens at http://localhost:5173
```

> **Note**: The backend must be running on port 8000 for the frontend to connect to the API.

### 3. Production build (optional)
```bash
npm run build
# Output in frontend/dist/
```

---

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
# Expected: 55 passed
```

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `development` | Environment name |
| `DEBUG` | `true` | Enable verbose SQL + logging |
| `PORT` | `8000` | API server port |
| `DATABASE_URL` | *(SQLite)* | Override for PostgreSQL |
| `OPENWEATHER_API_KEY` | — | Phase 4: live weather |
| `ELECTRICITY_PRICE_API_KEY` | — | Phase 4: live pricing |
| `OPENAI_API_KEY` | — | Phase 4: LLM explanations |

---

## Switching to PostgreSQL (Production)

1. Install async driver: `pip install asyncpg`
2. Set env var: `DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/ev_charging`
3. Run migrations: `python -m alembic upgrade head`

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: pulp` | `pip install pulp[cbc]` |
| `No such table: charging_sessions` | Run `python -m alembic upgrade head` |
| ML model not found | Run `python ml/train.py` |
| Frontend can't reach API | Make sure backend is on port 8000 |
| CORS error | Backend CORS is pre-configured for localhost:5173 |
