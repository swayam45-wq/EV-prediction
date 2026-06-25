# 05. API Reference

All backend endpoints are RESTful, fully validated with Pydantic v2 schemas, and return JSON responses.

---

## Core Optimization: `POST /api/recommend`

Generates an optimized bidirectional (charging & discharging) schedule and wear estimates.

### Request Body (JSON)
| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| `current_soc` | float | Yes | Current battery percentage (0-100) | `30.0` |
| `target_soc` | float | Yes | Desired battery percentage (0-100) | `80.0` |
| `battery_capacity_kwh` | float | Yes | Usable battery capacity | `75.0` |
| `max_charge_rate_kw` | float | Yes | Maximum charger draw | `11.0` |
| `battery_health_soh` | float | Yes | Battery State of Health % | `95.0` |
| `departure_time` | string | Yes | HH:MM format | `"08:00"` |
| `electricity_prices` | array | Yes | Hourly dynamic price array | *(see below)* |
| `temperature_celsius` | float | No | Ambient temperature (Celsius) | `22.0` |
| `weather_condition` | string | No | e.g. "clear", "cloudy", "rain" | `"clear"` |
| `charging_efficiency` | float | No | Grid-to-battery efficiency (default 0.90) | `0.90` |
| `v2g_enabled` | boolean | No | Enable vehicle-to-grid grid sellback | `false` |

### Response Body (JSON)
```json
{
  "status": "optimal",
  "start_charging": "01:00",
  "stop_charging": "05:00",
  "schedule": [
    {
      "hour": "00:00",
      "price": 0.08,
      "energy_kwh": 0.0,
      "is_charging": false,
      "cumulative_soc": 30.0
    },
    {
      "hour": "01:00",
      "price": 0.07,
      "energy_kwh": 11.0,
      "is_charging": true,
      "cumulative_soc": 43.2
    }
  ],
  "total_energy_kwh": 41.67,
  "target_soc_reached": true,
  "cost_analysis": {
    "normal_cost": 7.42,
    "optimized_cost": 3.12,
    "savings_dollar": 4.30,
    "savings_percent": 57.95
  },
  "wear_estimate": {
    "total_score": 1.25,
    "rating": "Low",
    "temperature_impact": 0.8,
    "high_soc_stress": 0.2,
    "fast_charging_penalty": 0.25
  },
  "battery_health_advice": [
    "✅ Battery temperature is optimal for charging.",
    "✓ Keep battery target at 80% to maximize lifetime."
  ],
  "explanations": [
    "⏰ Charging scheduled from 01:00 to 05:00.",
    "💰 Shuffled charging to cheapest hours when prices are 40% below average."
  ]
}
```

---

## Live Data Feeds

### `GET /api/weather`
Fetches real-time weather information and compiles charging modifiers.
- **Query Params**: `city` (optional, string)
- **Response**:
  ```json
  {
    "status": "success",
    "live_data": {
      "source": "openweathermap",
      "city": "Mumbai",
      "temperature_celsius": 30.5,
      "weather_condition": "Rain",
      "humidity_pct": 90,
      "wind_speed_ms": 4.2
    },
    "adjustments": {
      "temperature_celsius": 30.5,
      "weather_condition": "rain",
      "efficiency_modifier": 0.95,
      "solar_opportunity": false,
      "warnings": ["🌧️ Rain detected. Inspect charge port seals for moisture."],
      "recommendations": ["Optimize scheduling using rain-adjusted efficiency values."]
    }
  }
  ```

### `GET /api/prices`
Fetches the 24-hour pricing schedule for a specified regional utility model.
- **Query Params**: `region` (optional, e.g., `US_CA`, `US_TX`, `UK`, `DE`, `IN`)
- **Response**:
  ```json
  {
    "status": "success",
    "region": "US_CA",
    "prices": [
      {"hour": "00:00", "price": 0.08},
      {"hour": "01:00", "price": 0.07}
    ],
    "avg_price": 0.145,
    "peak_price": 0.24,
    "peak_hour": "18:00",
    "off_peak_price": 0.06,
    "off_peak_hour": "03:00",
    "currency": "USD"
  }
  ```

---

## Vehicle Telemetry APIs

### `GET /api/vehicle/status`
Fetches current vehicle telemetry for auto-filling inputs.
- **Query Params**: `provider` (optional, string to force e.g. `demo`, `smartcar`, `tesla`)
- **Response**:
  ```json
  {
    "source": "demo",
    "connected": true,
    "vehicle_id": "DEMO-001",
    "make": "ChargeMind",
    "model": "EV Demo · 75 kWh",
    "battery_level_pct": 68.0,
    "battery_range_km": 316.0,
    "battery_capacity_kwh": 75.0,
    "is_plugged_in": true,
    "charge_state": "NOT_CHARGING",
    "charge_rate_kw": 0.0,
    "battery_health_soh": 94.0
  }
  ```

### `GET /api/vehicle/connect`
Initiates Smartcar OAuth 2.0 connection.
- **Response**:
  ```json
  {
    "status": "ready",
    "authorization_url": "https://connect.smartcar.com/oauth/authorize?response_type=code&...",
    "instructions": "Open the authorization_url in your browser to connect your car."
  }
  ```

### `DELETE /api/vehicle/disconnect`
Disconnects active vehicle links and reverts the server back to demo mode.
- **Response**:
  ```json
  {
    "status": "disconnected",
    "message": "Vehicle disconnected. Demo mode active."
  }
  ```

### `GET /api/vehicle/providers`
Lists configured telemetry connections.
- **Response**:
  ```json
  {
    "providers": [
      {"id": "demo", "name": "Demo Mode", "configured": true},
      {"id": "smartcar", "name": "Smartcar", "configured": false}
    ],
    "active_provider": "demo"
  }
  ```

---

## History & Analytics

### `GET /api/battery-health`
Returns SoH percentages, health tips, and ML model wear logs.
- **Response**:
  ```json
  {
    "status": "success",
    "summary": {
      "total_charging_sessions": 12,
      "avg_wear_score": 1.45,
      "avg_savings_percent": 34.2,
      "total_energy_charged_kwh": 482.0,
      "inferred_soh_percent": 94.8
    },
    "wear_history": [
      {
        "session_id": 1,
        "wear_score": 1.12,
        "wear_rating": "Low",
        "target_soc": 80,
        "temperature": 21.0,
        "created_at": "2026-06-25T12:00:00Z"
      }
    ]
  }
  ```

### `GET /api/analytics`
Compiles session aggregates, savings profiles, charging times, and SoC distributions for charts.
- **Response**:
  ```json
  {
    "status": "success",
    "session_count": 12,
    "total_saved_usd": 48.5,
    "savings_trend": [
      {"date": "06/25", "savings_percent": 34.2, "optimized_cost": 4.12, "normal_cost": 6.25}
    ],
    "wear_trend": [
      {"date": "06/25", "wear_score": 1.12, "rating": "Low"}
    ]
  }
  ```
