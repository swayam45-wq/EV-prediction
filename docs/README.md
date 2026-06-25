# 📖 Documentation — AI-Powered Smart EV Charging Recommendation System

Welcome to the project documentation. This folder contains everything you need to understand, run, and extend the system.

## 📑 Table of Contents

| Document | Description |
|----------|-------------|
| [01_project_overview.md](./01_project_overview.md) | Problem statement, goals, and high-level system design |
| [02_architecture.md](./02_architecture.md) | System architecture, data flow, and component diagram |
| [03_optimization_engine.md](./03_optimization_engine.md) | Deep dive into the LP optimizer — math, constraints, and how it works |
| [04_battery_degradation_model.md](./04_battery_degradation_model.md) | Battery wear scoring — the science and the code |
| [04b_ml_model_phase2.md](./04b_ml_model_phase2.md) | ML wear prediction pipeline (XGBoost vs. RandomForest) |
| [05_api_reference.md](./05_api_reference.md) | Complete API documentation with request/response examples |
| [05b_setup_guide.md](./05b_setup_guide.md) | Detailed installation and environment troubleshooting guide |
| [06_frontend_phase3.md](./06_frontend_phase3.md) | Guide to React dashboard pages, custom CSS design system, and telemetry views |
| [06_setup_and_installation.md](./06_setup_and_installation.md) | Quickstart guide to install and run locally |
| [07_testing_guide.md](./07_testing_guide.md) | How to run tests and what each test covers |
| [08_roadmap.md](./08_roadmap.md) | Completed and future phases overview |

## 🚀 Quick Links

- **GitHub Repo**: [github.com/swayam45-wq/EV-prediction](https://github.com/swayam45-wq/EV-prediction)
- **API Docs (when running)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Run the server**: `cd backend && python -m uvicorn main:app --reload --port 8000`
- **Run tests**: `cd backend && python -m pytest tests/ -v`
