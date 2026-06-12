# 07. Testing Guide

The project includes a comprehensive test suite using `pytest`. Testing is crucial for ensuring the LP optimizer behaves correctly under various constraints and edge cases.

## Running Tests

Ensure your virtual environment is activated and you are in the `backend` directory.

### Run all tests:
```bash
python -m pytest tests/ -v
```

### Run tests with a shorter traceback (easier to read if a test fails):
```bash
python -m pytest tests/ -v --tb=short
```

### Run a specific test file:
```bash
python -m pytest tests/test_optimizer.py -v
```

## Test Suite Overview (29 Tests)

The tests are located in `backend/tests/` and are broken down into three main files:

### 1. `test_optimizer.py` (The LP Solver)
Verifies that the math engine is working correctly.
*   **Basic Scenarios:** Ensures it correctly meets the target SoC and stops charging when the battery is full.
*   **Cost Minimization:** Strictly verifies that the solver allocates energy to the cheapest available hourly slots.
*   **Edge Cases:** Tests what happens if the time limit is too short to reach the target charge (must return `infeasible`), handles uniform prices correctly, and accounts for battery State of Health (SoH) reducing usable capacity.

### 2. `test_degradation.py` (The Battery Wear Model)
Verifies the heuristic scoring logic.
*   Ensures extreme heat and cold trigger appropriate penalty scores.
*   Ensures charging to 100% yields a higher stress score than charging to 80%.
*   Ensures high C-rates (fast charging) increase the penalty.
*   Validates the `compare_wear_scenarios` utility.

### 3. `test_api.py` (Integration Tests)
Verifies the FastAPI endpoints end-to-end using `httpx.TestClient`.
*   Sends valid JSON payloads and asserts the structure and logic of the `ChargingRecommendation` response.
*   Tests error handling for invalid payloads (e.g., target SoC lower than current SoC).
*   Ensures Pydantic validation catches missing or malformed data, returning a `422` status.
*   Verifies that health checks and stub endpoints return `200 OK`.
