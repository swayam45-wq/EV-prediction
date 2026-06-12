# 08. Roadmap

This project is being developed in four phases. Phase 1 (Backend Baseline) is complete.

## ✅ Phase 1: Backend Baseline (Current)
- Complete FastAPI backend architecture.
- Pydantic validation schemas.
- **LP Optimization Engine** (PuLP/CBC) for cost minimization.
- Rule-based **Battery Degradation Model** (temperature, SoC, C-rate).
- Naive vs. Optimized cost analysis.
- Rule-based AI Recommendation Engine for explanations.
- 100% passing test suite.

## 🔜 Phase 2: ML Model & Database Layer
**Focus:** Replace heuristics with machine learning and add persistence.
1.  **Dataset Generation:** Create synthetic charging session data.
2.  **ML Degradation Model:** Train models (XGBoost, LightGBM) to predict battery wear scores.
3.  **ML Integration:** Replace the heuristic `battery_degradation.py` logic with the trained model inference.
4.  **Database Integration:** Setup PostgreSQL and SQLAlchemy.
5.  **History Tracking:** Store charging sessions, schedules, and analytics.

## 🚧 Phase 3: Frontend Dashboard
**Focus:** User Interface.
1.  **Tech Stack Setup:** React, TypeScript, Tailwind CSS, Vite.
2.  **Home Page:** Live battery status, current price ticker.
3.  **Optimizer Interface:** Form inputs for user constraints, charting for the hourly schedule and prices (Chart.js/Recharts).
4.  **Battery Health & Analytics:** Visualizing historical degradation trends and total money saved.

## 🚀 Phase 4: Advanced Features
**Focus:** Real-world API integration and advanced capabilities.
1.  **Live Pricing APIs:** Connect to utility dynamic pricing APIs.
2.  **Weather APIs:** Use OpenWeatherMap for real-time temperature data.
3.  **Solar Integration:** Allow users to input solar generation forecasts to optimize self-consumption.
4.  **V2G (Vehicle-to-Grid):** Add optimization capabilities to sell energy back to the grid during peak pricing.
5.  **LLM Integration:** Replace rule-based explanations with an LLM for personalized, conversational charging advice.
