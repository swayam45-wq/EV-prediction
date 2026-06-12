# 05. API Reference

The backend exposes a RESTful API built with FastAPI.

## Interactive Documentation

When the server is running, you can access interactive documentation (Swagger UI) at:
**http://localhost:8000/docs**

---

## Endpoint: `POST /api/recommend`

Generates the optimal charging schedule based on user constraints and dynamic pricing.

### Request Body (JSON)

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `current_soc` | float | Yes | Current battery % (0-100) | `35.0` |
| `target_soc` | float | Yes | Desired battery % (0-100) | `80.0` |
| `battery_capacity_kwh` | float | Yes | Total battery capacity | `75.0` |
| `max_charge_rate_kw` | float | Yes | Max charger power | `11.0` |
| `departure_time` | string | Yes | Time in HH:MM format | `"08:00"` |
| `electricity_prices` | array | Yes | Hourly price data | *(see below)* |
| `battery_health_soh` | float | No | State of Health % (default: 100) | `92.0` |
| `temperature_celsius` | float | No | Ambient temp (default: 25.0) | `28.0` |
| `weather_condition` | string | No | e.g., "clear", "rain" | `"clear"` |
| `charging_efficiency` | float | No | Wall-to-battery efficiency | `0.90` |

#### `electricity_prices` Array Structure:
```json
[
  {"hour": "00:00", "price": 0.12},
  {"hour": "01:00", "price": 0.10}
]
```

### Response Body (JSON)

Returns a `200 OK` on success.

```json
{
  "status": "optimal",
  "start_charging": "01:00",
  "stop_charging": "04:00",
  "schedule": [
    {
      "hour": "01:00",
      "price": 0.10,
      "energy_kwh": 11.0,
      "is_charging": true,
      "cumulative_soc": 48.2
    }
    // ... other slots
  ],
  "total_energy_kwh": 34.5,
  "target_soc_reached": true,
  "cost_analysis": {
    "normal_cost": 3.40,
    "optimized_cost": 2.68,
    "savings_dollar": 0.72,
    "savings_percent": 21.3
  },
  "wear_estimate": {
    "total_score": 2.3,
    "rating": "Low",
    "temperature_impact": 2.3,
    "high_soc_stress": 0.0,
    "fast_charging_penalty": 0.0
  },
  "battery_health_advice": [
    "✅ Current charging conditions are optimal for battery longevity."
  ],
  "explanations": [
    "⏰ Charging scheduled from 01:00 to 04:00.",
    "💵 This optimized schedule saves you $0.72 (21.3%) compared to charging immediately."
  ]
}
```

### Error Responses

*   **`400 Bad Request`**: Validation failed (e.g., target SoC <= current SoC).
*   **`422 Unprocessable Entity`**: Pydantic schema validation failed (e.g., missing required fields, invalid types) OR the LP optimizer determined the request is infeasible (e.g., impossible to charge that much energy in the time provided).

---

## Utility Endpoints

*   **`GET /`**: Welcome message and API status.
*   **`GET /health`**: Simple health check endpoint for monitoring.
*   **`GET /api/battery-health`**: Stub for Phase 2 battery health dashboard.
*   **`GET /api/analytics`**: Stub for Phase 2 historical analytics.
