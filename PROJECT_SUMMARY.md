# Project Summary — AI AQI Prediction System

## Complete File Inventory

### Backend (`backend/`)
```
backend/
├── app/
│   ├── __init__.py              ← App factory, extensions, JWT/error handlers, security headers, CLI
│   ├── api/v1/
│   │   ├── __init__.py          ← Blueprint registration
│   │   └── routes/
│   │       ├── auth.py          ← Register, login, JWT, forgot/reset, profile
│   │       ├── prediction.py    ← Predict, batch, explain, history
│   │       ├── dataset.py       ← Upload CSV, fetch OpenAQ
│   │       ├── analytics.py     ← Trend, city, pollutant stats
│   │       ├── reports.py       ← PDF/CSV downloads
│   │       ├── history.py       ← Historical readings browser
│   │       └── admin.py         ← Full admin CRUD
│   ├── core/
│   │   ├── config.py            ← Dev/test/prod config
│   │   ├── logging.py           ← Rotating file + console
│   │   ├── security.py          ← Headers, sanitise, tokens
│   │   └── cli.py               ← flask seed-db, create-admin, list-routes, db-status, purge-tokens
│   ├── models/
│   │   ├── role.py              ← 4 RBAC roles
│   │   ├── user.py              ← Users + bcrypt password
│   │   ├── refresh_token.py     ← JWT revocation
│   │   ├── dataset.py           ← Dataset metadata
│   │   ├── aqi_reading.py       ← Raw sensor readings
│   │   ├── ml_model.py          ← Trained model registry
│   │   ├── prediction.py        ← Prediction records + category helper
│   │   ├── report.py            ← Generated report metadata
│   │   └── audit_log.py         ← Immutable audit trail
│   ├── schemas/
│   │   ├── auth_schemas.py      ← Register, login, forgot/reset, change-password
│   │   ├── prediction_schemas.py← Prediction input, batch, explain
│   │   └── dataset_schemas.py   ← Dataset fetch/upload
│   ├── services/
│   │   ├── auth_service.py      ← Full auth business logic
│   │   ├── dataset_service.py   ← AQI calc, cleaning pipeline, OpenAQ
│   │   ├── prediction_service.py← ML prediction + SHAP
│   │   ├── analytics_service.py ← Aggregated analytics queries
│   │   └── report_service.py    ← PDF + CSV generation
│   ├── ml/
│   │   └── predictor.py         ← Singleton model loader
│   ├── xai/
│   │   └── explainer.py         ← SHAP TreeExplainer + LIME TabularExplainer
│   └── utils/
│       ├── audit.py             ← log_action() helper
│       ├── decorators.py        ← @require_roles, @admin_required
│       ├── email_utils.py       ← Transactional emails (reset, verify)
│       ├── validators.py        ← Email, password, username validators
│       └── response.py          ← success(), error(), paginated() helpers
├── migrations/
│   ├── env.py                   ← Alembic environment
│   ├── alembic.ini              ← Alembic config
│   └── script.py.mako           ← Migration template
├── tests/
│   ├── conftest.py              ← Fixtures: app, db, users, tokens
│   ├── unit/
│   │   ├── test_validators.py
│   │   ├── test_models.py
│   │   ├── test_dataset_cleaning.py
│   │   └── test_security.py
│   └── integration/
│       ├── test_auth_api.py
│       ├── test_prediction_api.py
│       ├── test_admin_api.py
│       └── test_analytics_api.py
├── .env.example
├── .flaskenv
├── Dockerfile
├── gunicorn.conf.py
├── pytest.ini
├── requirements.txt
└── run.py
```

### Frontend (`frontend/`)
```
frontend/
├── src/
│   ├── App.jsx                  ← Router with PrivateRoute/AdminRoute guards
│   ├── main.jsx                 ← ReactDOM root, Toaster
│   ├── styles/index.css         ← Tailwind + component classes
│   ├── pages/
│   │   ├── Landing.jsx          ← Public marketing page
│   │   ├── Login.jsx            ← JWT login form
│   │   ├── Register.jsx         ← Registration with role selection
│   │   ├── ForgotPassword.jsx
│   │   ├── ResetPassword.jsx
│   │   ├── VerifyEmail.jsx
│   │   ├── Dashboard.jsx        ← AQI overview, charts, recent predictions
│   │   ├── Prediction.jsx       ← Predict form + SHAP result panel
│   │   ├── Analytics.jsx        ← Area/bar/radar/heatmap charts + model table
│   │   ├── History.jsx          ← Paginated readings table
│   │   ├── Reports.jsx          ← PDF/CSV download buttons
│   │   ├── Profile.jsx          ← Profile edit + change password
│   │   ├── Settings.jsx         ← Notifications, defaults
│   │   ├── AdminPanel.jsx       ← 6-tab admin panel
│   │   └── NotFound.jsx         ← 404 page
│   ├── components/
│   │   ├── common/
│   │   │   ├── Layout.jsx       ← Sidebar + Navbar wrapper
│   │   │   ├── Sidebar.jsx      ← Navigation with role-gated links
│   │   │   ├── Navbar.jsx       ← Top bar with user avatar
│   │   │   ├── LoadingSpinner.jsx
│   │   │   ├── StatCard.jsx
│   │   │   ├── Pagination.jsx
│   │   │   ├── Badge.jsx
│   │   │   ├── EmptyState.jsx
│   │   │   └── ConfirmDialog.jsx
│   │   ├── charts/
│   │   │   ├── AQIGauge.jsx     ← Semi-circle gauge
│   │   │   ├── TrendChart.jsx   ← Area/line chart with min/max
│   │   │   ├── PollutantChart.jsx ← Bar chart with WHO limits
│   │   │   └── HeatmapChart.jsx ← CSS heatmap grid
│   │   ├── dashboard/
│   │   │   ├── AQICard.jsx      ← AQI hero card with colour ring
│   │   │   ├── HealthAdvisory.jsx ← Contextual health tips
│   │   │   ├── WeatherWidget.jsx ← Temperature, humidity, wind
│   │   │   └── RecentPredictions.jsx
│   │   └── admin/
│   │       ├── UserTable.jsx    ← Reusable user management table
│   │       └── DatasetTable.jsx ← Reusable dataset table
│   ├── hooks/
│   │   ├── useAQI.js            ← Prediction + analytics data hook
│   │   ├── useDebounce.js
│   │   ├── usePagination.js
│   │   └── useLocalStorage.js
│   ├── services/
│   │   ├── api.js               ← Axios + JWT interceptors + auto-refresh
│   │   ├── authService.js
│   │   ├── predictionService.js
│   │   ├── analyticsService.js
│   │   └── adminService.js
│   ├── store/
│   │   └── authStore.js         ← Zustand auth state
│   └── utils/
│       ├── aqiUtils.js          ← AQI colour/badge/category helpers
│       ├── formatters.js        ← Number, date, pollutant formatters
│       └── constants.js         ← AQI categories, pollutants, roles
├── public/
│   ├── favicon.svg
│   └── robots.txt
├── .env.example
├── Dockerfile
├── nginx.conf
├── package.json
├── postcss.config.js
├── tailwind.config.js
├── vercel.json
└── vite.config.js
```

### ML (`ml/`)
```
ml/
├── notebooks/
│   ├── 01_EDA_AQI_Analysis.py   ← Full EDA (distributions, trends, correlations, heatmaps)
│   └── 02_Model_Evaluation.py   ← Actual vs predicted, residuals, CV, feature importance
├── scripts/
│   ├── train_models.py          ← Train 6 models, auto-select best, save artefacts
│   └── predict_sample.py        ← Demo predictions without Flask API
├── models/                      ← aqi_model.pkl, scaler.pkl, feature_names.json (generated)
├── data/
│   ├── raw/                     ← Input CSVs or synthetic data
│   └── processed/               ← eda_cleaned.csv (generated)
└── reports/                     ← All EDA + evaluation PNG plots (generated)
```

### Infrastructure
```
database/
├── schema.sql                   ← Full MySQL DDL with indexes and constraints
└── seeds/
    ├── 01_seed_roles.sql
    └── 02_seed_admin.sql

diagrams/
├── ER_DIAGRAM.md
├── USE_CASE_DIAGRAM.md
└── SEQUENCE_DIAGRAM.md

docs/
├── API_GUIDE.md
├── ARCHITECTURE.md
├── DEVELOPER_GUIDE.md
└── USER_MANUAL.md

.github/workflows/ci.yml         ← Pytest + ESLint + Docker build CI
docker-compose.yml               ← db + backend + frontend + adminer
.dockerignore / .gitignore
setup.bat / setup.sh             ← One-command local setup
README.md
PROJECT_SUMMARY.md               ← This file
```

## Quick Start

```bash
# Windows
setup.bat

# Linux/macOS
chmod +x setup.sh && ./setup.sh

# Docker
docker compose up --build -d
docker exec aqi_backend flask db upgrade
docker exec aqi_backend flask seed-db
```

## Default Credentials

After running setup:
- **Admin:** `admin@aqisystem.local` / `Admin@12345`
- Change this password immediately via Admin Panel → Users.

## Technology Decisions

| Decision | Rationale |
|---|---|
| XGBoost as default model | Consistently best RMSE/R² on tabular AQI data, fast training, supports SHAP TreeExplainer |
| SHAP TreeExplainer | Exact (not approximate) for tree models, 100x faster than KernelExplainer |
| JWT with refresh tokens | Stateless auth + revocation support via DB-stored refresh tokens |
| Zustand over Redux | Minimal boilerplate for auth-only global state; everything else is local |
| fpdf2 for PDF | Pure Python, no system dependencies like wkhtmltopdf |
| SQLAlchemy 2.x | Type-safe ORM with async support path for future scaling |
| Gunicorn sync workers | Simpler than async for CPU-bound ML inference; add async worker class for I/O scaling |
