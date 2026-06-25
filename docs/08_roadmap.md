# 08. Roadmap

All development phases are complete, transforming the EV Charging system from a backend simulator into a fully integrated, live-connected automotive dashboard.

## ✅ Phase 1: Backend Baseline
- Complete FastAPI backend architecture.
- Pydantic validation schemas.
- **LP Optimization Engine** (PuLP/CBC) for cost minimization.
- Rule-based **Battery Degradation Model** (temperature, SoC, C-rate).
- Naive vs. Optimized cost analysis.
- Rule-based AI Recommendation Engine for explanations.
- 100% passing test suite.

## ✅ Phase 2: ML Model & Database Layer
- **Dataset Generation:** Created 15,000 synthetic charging sessions.
- **ML Degradation Model:** Trained and evaluated RandomForest and XGBoost (achieved $R^2 = 0.993$).
- **ML Integration:** Integrated model inference inside the optimization pipeline.
- **Database Integration:** Integrated async SQLite (`aiosqlite`) + SQLAlchemy ORM.
- **History Tracking:** Stored completed sessions, schedules, and historical analytics.

## ✅ Phase 3: Frontend Dashboard
- **React + TS + Tailwind v4**: Implemented high-density automotive dark dashboard.
- **Home Page**: Circular SoC gauge, battery metrics, active charging conditions.
- **Optimizer Page**: Interactive LP form input + Chart.js schedule and price visualizations.
- **Battery Health Page**: SOH ring, wear trends, session logs.
- **Analytics Page**: Savings trends, charge hour counts, SoC distributions.

## ✅ Phase 4 & 4b: Live Telemetry & Advanced Features
- **Live Weather Feed**: Integrated OpenWeatherMap API with humidity-aware component warnings.
- **Dynamic Pricing Profiles**: Created 5 TOU tariffs (CA, TX, UK, DE, IN) with a region selector dropdown.
- **Vehicle Telemetry API**: Connected vehicle telemetry via Smartcar OAuth 2.0 (works with 30+ brands like Tesla, Ford, BMW, VW, Rivian) and Tesla Fleet API.
- **UI Action Flows**: Designed connect/disconnect buttons and live battery status/charging banners.
- **Vehicle-to-Grid (V2G)**: Extended LP formulation to schedule grid sell-back during peak hours.
- **Expanded Tests**: Added 7 new telemetry API tests, raising total passing tests to 62.
