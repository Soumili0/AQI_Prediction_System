# System Architecture

## Overview

The system follows a three-tier architecture:

```
┌──────────────────────────────────────────────────────────────┐
│  PRESENTATION TIER  — React 18 SPA (Vite + Tailwind)         │
│  Pages: Landing, Dashboard, Prediction, Analytics,           │
│         History, Reports, Profile, Settings, Admin           │
│  State: Zustand (auth) + local useState                      │
│  Charts: Recharts (line, bar, area, pie, radar)              │
└────────────────────────┬─────────────────────────────────────┘
                         │ REST JSON over HTTP(S)
                         │ JWT Bearer tokens
┌────────────────────────▼─────────────────────────────────────┐
│  APPLICATION TIER  — Flask 3 + Gunicorn                      │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │   Auth   │  │ Predict  │  │Analytics │  │   Admin    │  │
│  │  Routes  │  │  Routes  │  │  Routes  │  │   Routes   │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬──────┘  │
│       │              │              │               │         │
│  ┌────▼──────────────▼──────────────▼───────────────▼─────┐  │
│  │               Service Layer (Business Logic)           │  │
│  │  AuthService · PredictionService · AnalyticsService    │  │
│  │  DatasetService · ReportService                        │  │
│  └──────────┬───────────────────────┬─────────────────────┘  │
│             │                       │                         │
│  ┌──────────▼────────┐  ┌───────────▼──────────────────────┐ │
│  │   ML Engine        │  │       Data Access Layer          │ │
│  │  AQIPredictor      │  │  SQLAlchemy ORM Models           │ │
│  │  (singleton)       │  │  User · Prediction · Dataset     │ │
│  │                   │  │  AQIReading · MLModel · Report    │ │
│  │  XAI Engine        │  │  AuditLog · Role · RefreshToken  │ │
│  │  SHAP + LIME       │  └──────────────────────────────────┘ │
│  └───────────────────┘                                        │
└────────────────────────┬─────────────────────────────────────┘
                         │ SQLAlchemy / mysqlclient
┌────────────────────────▼─────────────────────────────────────┐
│  DATA TIER  — MySQL 8.0                                      │
│  Tables: roles, users, refresh_tokens, datasets,            │
│          aqi_readings, ml_models, predictions,              │
│          reports, audit_logs                                 │
└──────────────────────────────────────────────────────────────┘
```

---

## Request Lifecycle — AQI Prediction

```
Browser
  │
  ├─ POST /api/v1/predictions/  { pm25: 85, pm10: 120, ... }
  │
Flask Router
  │
  ├─ JWT optional verification (anonymous allowed)
  ├─ Rate limiter check (60/hour)
  │
prediction_bp.predict()
  │
  ├─ prediction_service.predict_aqi(data, user_id)
  │     │
  │     ├─ Validate required fields
  │     ├─ Enrich with time features (hour, month, season…)
  │     ├─ get_predictor()  ← singleton load on first call
  │     │     └─ joblib.load(aqi_model.pkl)
  │     │     └─ joblib.load(scaler.pkl)
  │     │
  │     ├─ scaler.transform(feature_vector)
  │     ├─ model.predict(scaled_vector)  → AQI float
  │     │
  │     ├─ get_aqi_category(aqi)  → category + advisory
  │     │
  │     ├─ explain_shap(model, X_scaled, feature_names)
  │     │     └─ TreeExplainer.shap_values()
  │     │     └─ generate_waterfall_plot() → base64 PNG
  │     │
  │     └─ db.session.add(Prediction record)
  │
  └─ JSON response  { predicted_aqi, category, advisory, explanation }
  │
Browser renders AQI gauge + SHAP waterfall chart
```

---

## Database Entity Relationships

```
roles ──────────< users
                    │
                    ├──────────< refresh_tokens
                    ├──────────< datasets ──────< aqi_readings
                    ├──────────< predictions
                    ├──────────< reports
                    └──────────< audit_logs

ml_models ─────────< predictions
```

All foreign keys use InnoDB with `ON DELETE CASCADE` or `SET NULL` as appropriate.
Audit logs are append-only (no UPDATE or DELETE permissions in production).

---

## Security Architecture

```
Request
  │
  ├── CORS check (Flask-CORS, whitelist origins)
  ├── Rate limiting (Flask-Limiter, memory/Redis storage)
  ├── JWT verification (Flask-JWT-Extended)
  │     └── Checks: signature, expiry, revocation (refresh_tokens table)
  ├── RBAC check (@require_roles / @admin_required decorators)
  ├── Input validation (Marshmallow schemas)
  ├── SQL injection prevention (SQLAlchemy parameterised queries)
  └── Security headers (X-Frame-Options, CSP, HSTS via after_request hook)
```

**Password storage:** bcrypt with work factor 12 (auto-upgraded on login).
**Tokens:** JWT access (1 hour) + refresh (30 days). Refresh tokens stored in DB for revocation.
**Password reset:** time-limited signed token (1 hour), single-use, stored as plain token (hashed in production extension).

---

## ML Architecture

```
Raw Data (CSV / OpenAQ API)
  │
Cleaning Pipeline (dataset_service.py)
  ├── Normalise column names
  ├── Drop duplicates and empty rows
  ├── Parse datetime
  ├── Clip negative pollutant values
  ├── Remove outliers (IQR × 3)
  ├── Impute missing values (forward-fill → median)
  ├── Calculate AQI (US EPA breakpoints)
  └── Feature engineering (hour, month, season, is_weekend)
  │
train_test_split (80/20)
  │
StandardScaler (fit on train only, saved as scaler.pkl)
  │
6 Models trained in parallel
  ├── Linear Regression  (baseline)
  ├── Decision Tree      (interpretable)
  ├── Random Forest      (200 estimators)
  ├── XGBoost            (500 rounds, early stopping)
  ├── LightGBM           (500 rounds, early stopping)
  └── LSTM               (2-layer, 100 epochs, early stopping)
  │
Auto-select best by RMSE on test set
  │
Save: aqi_model.pkl · scaler.pkl · feature_names.json
```

---

## Deployment Architecture

```
                  ┌─────────────────┐
  Users ──HTTPS──► Vercel CDN       │  (React SPA, static files)
                  └────────┬────────┘
                           │ /api/* proxy
                  ┌────────▼────────┐
                  │ Render.com      │  (Flask + Gunicorn, 4 workers)
                  │ Web Service     │
                  └────────┬────────┘
                           │ MySQL connector
                  ┌────────▼────────┐
                  │ Railway / Aiven │  (MySQL 8 managed DB)
                  └─────────────────┘

CI/CD: GitHub Actions → pytest + eslint + docker build → auto-deploy on main
```
