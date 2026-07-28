# API Reference Guide

Base URL: `http://localhost:5000/api/v1`
Interactive docs: `http://localhost:5000/api/docs/`

## Authentication

All protected endpoints require a Bearer token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Tokens expire after 1 hour. Use the refresh endpoint to obtain a new one.

---

## Auth Endpoints

### POST /auth/register
Create a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "username": "john_doe",
  "password": "SecurePass@1",
  "first_name": "John",
  "last_name": "Doe",
  "role": "citizen",
  "city": "Delhi",
  "country": "India"
}
```
**Response 201:**
```json
{ "user": { "id": 1, "email": "user@example.com", "role": "citizen", ... }, "message": "..." }
```

---

### POST /auth/login
**Request:** `{ "email": "...", "password": "..." }`

**Response 200:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "Bearer",
  "user": { "id": 1, "email": "...", "role": "citizen" }
}
```

---

### POST /auth/refresh
Requires `Authorization: Bearer <refresh_token>`

**Response 200:** `{ "access_token": "eyJ...", "token_type": "Bearer" }`

---

### POST /auth/logout
Requires `Authorization: Bearer <refresh_token>`. Revokes the token.

---

### POST /auth/forgot-password
`{ "email": "user@example.com" }` — always returns 200 (prevents enumeration).

---

### POST /auth/reset-password
`{ "token": "<reset_token>", "new_password": "NewPass@1" }`

---

### GET /auth/me
Returns the current user's profile. Requires access token.

### PUT /auth/me
Update profile fields: `first_name`, `last_name`, `username`, `phone`, `city`, `country`, `organization`, `avatar_url`.

### PUT /auth/me/change-password
`{ "current_password": "...", "new_password": "..." }`

---

## Prediction Endpoints

### POST /predictions/
Predict AQI. Authentication optional (anonymous allowed).

**Required fields:** `pm25`, `pm10`, `no2`, `so2`, `co`, `o3`

**Full request:**
```json
{
  "pm25": 85.5, "pm10": 120.0, "no2": 45.2,
  "so2": 18.3,  "co": 1.2,     "o3": 60.0,
  "nh3": 12.0,  "temperature": 28.5,
  "humidity": 65.0, "wind_speed": 3.2, "pressure": 1013.0,
  "city": "Delhi"
}
```

**Response 200:**
```json
{
  "id": 42,
  "predicted_aqi": 142.5,
  "aqi_category": "Unhealthy for Sensitive Groups",
  "health_advisory": "Sensitive groups may experience health effects.",
  "input_features": { ... },
  "explanation": {
    "method": "shap",
    "base_value": 98.3,
    "feature_importance": { "pm25": 0.45, "pm10": 0.22, "no2": 0.11 },
    "waterfall_plot_b64": "<base64 PNG string>"
  },
  "requested_at": "2025-01-01T12:00:00",
  "model": "XGBoost"
}
```

---

### POST /predictions/batch
Requires auth. Up to 500 records.

```json
{ "records": [ { "pm25": 85, "pm10": 120, ... }, ... ] }
```

---

### GET /predictions/history
Requires auth. Params: `page`, `per_page`.

---

### GET /predictions/{id}
Get one prediction by ID. Requires auth (owner or admin).

---

### POST /predictions/explain
Full SHAP + LIME explanation.

```json
{ "features": { "pm25": 85, ... }, "methods": ["shap", "lime"] }
```

---

## Analytics Endpoints

All analytics endpoints are public (no auth required).

### GET /analytics/overview
Params: `city`, `days` (default 30)

Returns: `mean_aqi`, `min_aqi`, `max_aqi`, `current_aqi`, `total_readings`, `category_breakdown`

### GET /analytics/trend
Params: `city`, `granularity` (daily/monthly/yearly), `days`

Returns: `trend` array with `{ date, mean, min, max, count }`

### GET /analytics/cities
Returns mean/min/max AQI per city.

### GET /analytics/pollutants
Params: `city`, `days`. Returns average concentration for each pollutant.

### GET /analytics/models
Requires auth. Returns all trained ML models with metrics.

### GET /analytics/prediction-stats
Requires auth. Returns prediction count and category breakdown.

---

## Dataset Endpoints

### POST /datasets/upload
Multipart form. Requires auth.

Fields: `file` (CSV/XLSX), `name`, `description`, `location`, `is_public`

### POST /datasets/fetch-openaq
Requires auth (researcher or admin).

```json
{ "city": "Delhi", "country": "IN", "date_from": "2024-01-01", "date_to": "2024-01-31" }
```

### GET /datasets/
List accessible datasets. Params: `include_public` (bool).

### DELETE /datasets/{id}
Delete a dataset (owner or admin).

### GET /datasets/{id}/readings
Params: `page`, `per_page`. Paginated sensor readings for a dataset.

---

## Report Endpoints

### POST /reports/prediction-history
Requires auth.

```json
{ "format": "pdf", "city": "Delhi", "date_from": "2024-01-01", "date_to": "2024-12-31" }
```
Returns file download (PDF or CSV).

### POST /reports/analytics
```json
{ "format": "csv", "city": "Delhi", "days": 30 }
```

---

## Admin Endpoints
All require admin role.

| Method | Endpoint | Description |
|---|---|---|
| GET | /admin/stats | System-wide counts |
| GET | /admin/users | Paginated user list (params: `page`, `per_page`, `role`, `search`) |
| PUT | /admin/users/{id} | Update role or status |
| DELETE | /admin/users/{id} | Deactivate user |
| GET | /admin/datasets | All datasets |
| DELETE | /admin/datasets/{id} | Force delete any dataset |
| GET | /admin/predictions | All predictions |
| GET | /admin/models | All trained models |
| PUT | /admin/models/{id}/activate | Set active production model |
| GET | /admin/audit-logs | Audit trail (params: `action`, `user_id`) |

---

## Error Response Format

All errors follow:
```json
{ "error": "Human-readable message", "code": "OPTIONAL_CODE" }
```

| Status | Meaning |
|---|---|
| 400 | Validation error or bad input |
| 401 | Missing or invalid token |
| 403 | Insufficient role permissions |
| 404 | Resource not found |
| 429 | Rate limit exceeded |
| 503 | ML model not loaded (run training first) |
| 500 | Internal server error |
