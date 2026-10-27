# 🌍 AI-Based Air Quality Index Prediction System
### Explainable Environmental Analytics Using Public Sensor Data

[![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)](https://python.org)[![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)](https://flask.palletsprojects.com)
[![React](https://img.shields.io/badge/React-18-61dafb?logo=react)](https://react.dev)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-orange?logo=mysql)](https://mysql.com)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.0-red)](https://xgboost.readthedocs.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Tech Stack](#3-tech-stack)
4. [Project Structure](#4-project-structure)
5. [Prerequisites](#5-prerequisites)
6. [Quick Start with Docker](#6-quick-start-with-docker)
7. [Manual Installation](#7-manual-installation)
   - [Backend Setup](#71-backend-setup)
   - [Database Setup](#72-database-setup)
   - [Frontend Setup](#73-frontend-setup)
   - [ML Training](#74-ml-training)
8. [Environment Variables](#8-environment-variables)
9. [API Documentation](#9-api-documentation)
10. [Machine Learning Models](#10-machine-learning-models)
11. [Explainable AI (XAI)](#11-explainable-ai-xai)
12. [User Roles & Permissions](#12-user-roles--permissions)
13. [Running Tests](#13-running-tests)
14. [Deployment](#14-deployment)
15. [Contributing](#15-contributing)

---

## 1. Project Overview

The **AI-Based AQI Prediction System** is a production-ready, full-stack web application that:

- **Predicts** the Air Quality Index (AQI) from pollutant and weather sensor readings using multiple ML models (XGBoost, Random Forest, LSTM, and more).
- **Explains** every prediction with SHAP waterfall plots and LIME feature importance — making the AI transparent and trustworthy.
- **Visualises** historical trends, seasonal patterns, city comparisons, and pollutant heatmaps on an interactive dashboard.
- **Supports** four user roles — Citizen, Researcher, Policy Maker, Admin — with JWT-based authentication and role-based access control.
- **Generates** downloadable PDF and CSV reports for analytical and policy use.
- **Integrates** with the OpenAQ public sensor API and supports CSV/XLSX dataset uploads.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        BROWSER (React SPA)                       │
│  Landing · Login · Dashboard · Prediction · Analytics · Admin    │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS / REST JSON
┌────────────────────────────▼────────────────────────────────────┐
│                    FLASK REST API  (Gunicorn)                    │
│  /api/v1/auth  /predictions  /datasets  /analytics  /admin      │
│  JWT Auth · RBAC · Rate Limiting · Swagger UI · CORS            │
└───────┬──────────────┬────────────────┬────────────────────────-┘
        │              │                │
┌───────▼───┐   ┌──────▼──────┐  ┌─────▼──────────────────────┐
│  MySQL 8  │   │  ML Engine  │  │  XAI Engine                 │
│ (SQLAlch) │   │  XGBoost    │  │  SHAP (TreeExplainer)       │
│           │   │  RF · LGB   │  │  LIME (TabularExplainer)    │
│           │   │  LSTM(Keras)│  │  Waterfall · Force Plots    │
└───────────┘   └─────────────┘  └────────────────────────────-┘
```

**Data flow for a prediction request:**
1. React form → POST `/api/v1/predictions/`
2. Flask validates + enriches with time features
3. AQIPredictor singleton runs the trained model
4. SHAP TreeExplainer generates feature contributions
5. Result (AQI, category, advisory, SHAP plot) returned as JSON
6. React renders the AQI gauge, health advisory, and waterfall bar chart

---

## 3. Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React 18 + Vite | SPA, code splitting, fast HMR |
| Styling | Tailwind CSS | Utility-first responsive design |
| Charts | Recharts | Line, bar, area, pie, radar charts |
| State | Zustand | Lightweight global auth state |
| HTTP | Axios | API calls with JWT interceptors |
| Forms | React Hook Form + Yup | Validated input forms |
| Backend | Flask 3 + Gunicorn | REST API, WSGI server |
| ORM | SQLAlchemy 2 + Flask-Migrate | DB models, schema migrations |
| Auth | Flask-JWT-Extended | Access + refresh tokens |
| Security | Flask-Bcrypt, Flask-Limiter | Password hashing, rate limiting |
| Docs | Flasgger (Swagger UI) | Interactive API docs |
| Database | MySQL 8 | Relational data store |
| ML | Scikit-learn, XGBoost, LightGBM | AQI regression models |
| DL | TensorFlow/Keras | LSTM time-series model |
| XAI | SHAP, LIME | Prediction explanations |
| Data | Pandas, NumPy | Cleaning, feature engineering |
| Reports | fpdf2, openpyxl | PDF and Excel generation |
| Container | Docker + Docker Compose | Multi-service orchestration |
| CI/CD | GitHub Actions | Automated test + build pipeline |

---

## 4. Project Structure

```
AQI_Prediction_System/
│
├── backend/                        # Flask REST API
│   ├── app/
│   │   ├── __init__.py             # App factory (create_app)
│   │   ├── api/v1/routes/          # All route blueprints
│   │   │   ├── auth.py             # Register, login, JWT, forgot/reset password
│   │   │   ├── prediction.py       # AQI predict, batch, explain, history
│   │   │   ├── dataset.py          # CSV upload, OpenAQ fetch
│   │   │   ├── analytics.py        # Trend, city, pollutant analytics
│   │   │   ├── reports.py          # PDF/CSV report generation
│   │   │   ├── history.py          # Historical readings browser
│   │   │   └── admin.py            # User/dataset/model/audit management
│   │   ├── core/
│   │   │   ├── config.py           # Dev/test/prod config classes
│   │   │   ├── logging.py          # Rotating file + console logging
│   │   │   └── security.py         # Headers, sanitisation, token helpers
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   │   ├── user.py             # User + password hashing
│   │   │   ├── role.py             # RBAC roles
│   │   │   ├── prediction.py       # Prediction records + AQI categories
│   │   │   ├── dataset.py          # Dataset metadata
│   │   │   ├── aqi_reading.py      # Individual sensor readings
│   │   │   ├── ml_model.py         # Trained model registry
│   │   │   ├── report.py           # Generated report metadata
│   │   │   └── audit_log.py        # Immutable audit trail
│   │   ├── services/               # Business logic layer
│   │   │   ├── auth_service.py
│   │   │   ├── dataset_service.py  # Cleaning pipeline + AQI calculation
│   │   │   ├── prediction_service.py
│   │   │   ├── analytics_service.py
│   │   │   └── report_service.py
│   │   ├── ml/
│   │   │   └── predictor.py        # Singleton model loader
│   │   ├── xai/
│   │   │   └── explainer.py        # SHAP + LIME explanation engine
│   │   └── utils/
│   │       ├── audit.py            # Audit log helper
│   │       ├── decorators.py       # @require_roles, @admin_required
│   │       ├── email_utils.py      # Transactional emails (reset, verify)
│   │       └── validators.py       # Email, password, username validators
│   ├── tests/
│   │   ├── conftest.py             # Pytest fixtures, in-memory DB
│   │   ├── unit/                   # Validators, models, cleaning pipeline
│   │   └── integration/            # Auth, prediction, admin API tests
│   ├── requirements.txt
│   ├── run.py                      # Entry point
│   ├── pytest.ini
│   └── Dockerfile
│
├── frontend/                       # React 18 + Vite SPA
│   ├── src/
│   │   ├── pages/                  # 14 pages (Landing → Admin)
│   │   ├── components/common/      # Layout, Sidebar, Navbar, StatCard
│   │   ├── services/               # Axios API clients
│   │   ├── store/                  # Zustand auth store
│   │   ├── utils/                  # AQI colour/badge utilities
│   │   └── styles/index.css        # Tailwind + custom component classes
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── nginx.conf
│   └── Dockerfile
│
├── ml/
│   ├── notebooks/
│   │   └── 01_EDA_AQI_Analysis.py  # Full EDA pipeline (run as script)
│   ├── scripts/
│   │   └── train_models.py         # Train all 6 models, auto-select best
│   ├── models/                     # Saved artefacts (gitignored)
│   │   ├── aqi_model.pkl
│   │   ├── scaler.pkl
│   │   ├── feature_names.json
│   │   └── best_model_meta.json
│   ├── data/
│   │   ├── raw/                    # Input CSVs
│   │   └── processed/              # Cleaned data
│   └── reports/                    # EDA plots (PNG)
│
├── database/
│   ├── schema.sql                  # Full MySQL DDL
│   └── seeds/                      # Optional seed data
│
├── docs/                           # Additional documentation
├── diagrams/                       # Architecture and UML diagrams
├── docker-compose.yml
├── .dockerignore
├── .github/workflows/              # CI/CD pipeline
└── README.md
```

---

## 5. Prerequisites

| Technology | Version | Website |
|------------|---------|---------|
| Python | 3.13 | [python.org](https://python.org) |
| Node.js | 20 LTS | [nodejs.org](https://nodejs.org) |
| MySQL | 8.0 | [mysql.com](https://mysql.com) |
| Docker | 24 | [docker.com](https://docker.com) |
| Docker Compose | 2.20 | Bundled with Docker Desktop |

---

## 6. Quick Start with Docker

The fastest way to run the entire stack locally.

```bash
# 1. Clone the repository
git clone https://github.com/your-org/AQI_Prediction_System.git
cd AQI_Prediction_System

# 2. Copy and configure environment variables
cp backend/.env.example backend/.env
#    Edit backend/.env with your SECRET_KEY, JWT_SECRET_KEY, etc.

# 3. Train ML models first (runs outside Docker, generates ml/models/*.pkl)
cd backend
python -m pip install -r requirements.txt
cd ../ml/scripts
python train_models.py --no-lstm
cd ../..

# 4. Start all services
docker compose up --build -d

# 5. Run database migrations
docker exec aqi_backend flask db upgrade

# 6. Open the application
#    Frontend  → http://localhost
#    API Docs  → http://localhost:5000/api/docs/
#    Adminer   → http://localhost:8080  (use --profile dev)
```

To stop all services:
```bash
docker compose down
```

To stop and remove all data volumes:
```bash
docker compose down -v
```

---

## 7. Manual Installation

### 7.1 Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env — set DATABASE_URL, SECRET_KEY, JWT_SECRET_KEY at minimum

# Run database migrations
flask db init       # only the very first time
flask db migrate -m "Initial migration"
flask db upgrade

# Start the development server
flask run
# API available at http://localhost:5000
# Swagger UI at  http://localhost:5000/api/docs/
```

### 7.2 Database Setup

```sql
-- Run in MySQL client or via the schema file:
mysql -u root -p < database/schema.sql
```

The schema creates the `aqi_prediction_db` database with all tables, indexes, constraints, and seeds the four roles.

### 7.3 Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server (proxies /api to localhost:5000)
npm run dev
# App available at http://localhost:5173

# Build for production
npm run build
# Output in frontend/dist/
```

### 7.4 ML Training

```bash
cd ml/scripts

# Option A — use synthetic demo data (no dataset required)
python train_models.py

# Option B — use your own CSV
python train_models.py --data ../data/raw/your_dataset.csv

# Option C — skip LSTM (faster, no TensorFlow required)
python train_models.py --no-lstm

# Run EDA first to generate plots and cleaned data
python ../notebooks/01_EDA_AQI_Analysis.py
```

Trained artefacts are saved to `ml/models/`:
- `aqi_model.pkl` — best model (lowest RMSE)
- `scaler.pkl` — fitted StandardScaler
- `feature_names.json` — ordered feature list
- `model_comparison.csv` — metrics for all models
- `lstm_model/` — Keras SavedModel directory

---

## 8. Environment Variables

Copy `backend/.env.example` to `backend/.env` and set:

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes | Flask secret key (32+ random chars) |
| `JWT_SECRET_KEY` | Yes | JWT signing key (32+ random chars) |
| `DATABASE_URL` | Yes | `mysql+mysqlclient://user:pass@host:3306/db` |
| `MAIL_USERNAME` | No | Gmail address for transactional emails |
| `MAIL_PASSWORD` | No | Gmail app-specific password |
| `OPENAQ_API_KEY` | No | Key from [openaq.org](https://openaq.org) for sensor data |
| `CORS_ORIGINS` | No | Comma-separated allowed origins |
| `FLASK_ENV` | No | `development` / `production` |
| `LOG_LEVEL` | No | `DEBUG` / `INFO` / `WARNING` |

Generate secure keys:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 9. API Documentation

Interactive Swagger UI is available at **`http://localhost:5000/api/docs/`** when the backend is running.

### Authentication Endpoints

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/v1/auth/register` | Create account | Public |
| POST | `/api/v1/auth/login` | Get JWT tokens | Public |
| POST | `/api/v1/auth/refresh` | Rotate access token | Refresh token |
| POST | `/api/v1/auth/logout` | Revoke refresh token | Refresh token |
| POST | `/api/v1/auth/forgot-password` | Request reset link | Public |
| POST | `/api/v1/auth/reset-password` | Set new password | Public |
| POST | `/api/v1/auth/verify-email` | Verify email | Public |
| GET | `/api/v1/auth/me` | Get profile | Bearer |
| PUT | `/api/v1/auth/me` | Update profile | Bearer |
| PUT | `/api/v1/auth/me/change-password` | Change password | Bearer |

### Prediction Endpoints

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/v1/predictions/` | Predict AQI (single) | Optional |
| POST | `/api/v1/predictions/batch` | Predict AQI (batch, max 500) | Bearer |
| GET | `/api/v1/predictions/history` | User prediction history | Bearer |
| GET | `/api/v1/predictions/<id>` | Single prediction detail | Bearer |
| POST | `/api/v1/predictions/explain` | SHAP + LIME explanation | Bearer |

**Sample prediction request:**
```json
POST /api/v1/predictions/
{
  "pm25": 85.5,
  "pm10": 120.0,
  "no2": 45.2,
  "so2": 18.3,
  "co": 1.2,
  "o3": 60.0,
  "temperature": 28.5,
  "humidity": 65.0,
  "city": "Delhi"
}
```

**Sample response:**
```json
{
  "predicted_aqi": 142.5,
  "aqi_category": "Unhealthy for Sensitive Groups",
  "health_advisory": "Sensitive groups may experience health effects...",
  "explanation": {
    "method": "shap",
    "base_value": 98.3,
    "feature_importance": {
      "pm25": 0.45,
      "pm10": 0.22,
      "no2": 0.11,
      "o3": -0.08
    },
    "waterfall_plot_b64": "<base64 PNG>"
  },
  "requested_at": "2025-01-01T12:00:00"
}
```

### Analytics Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/analytics/overview` | AQI stats (mean, min, max, categories) |
| GET | `/api/v1/analytics/trend` | Time-series trend (daily/monthly/yearly) |
| GET | `/api/v1/analytics/cities` | City-wise AQI comparison |
| GET | `/api/v1/analytics/pollutants` | Average pollutant concentrations |
| GET | `/api/v1/analytics/models` | ML model comparison metrics |

### Dataset Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/datasets/upload` | Upload CSV/XLSX |
| POST | `/api/v1/datasets/fetch-openaq` | Fetch from OpenAQ API |
| GET | `/api/v1/datasets/` | List datasets |
| DELETE | `/api/v1/datasets/<id>` | Delete dataset |

### Report Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/reports/prediction-history` | Download prediction report (PDF/CSV) |
| POST | `/api/v1/reports/analytics` | Download analytics report (PDF/CSV) |

---

## 10. Machine Learning Models

Six models are trained and compared automatically:

| Model | Algorithm | Notes |
|---|---|---|
| Linear Regression | sklearn | Baseline |
| Decision Tree | sklearn | Interpretable, fast |
| Random Forest | sklearn | 200 estimators, n_jobs=-1 |
| XGBoost | xgboost | 500 rounds, early stopping |
| LightGBM | lightgbm | 500 rounds, early stopping |
| LSTM | TensorFlow/Keras | 2-layer stacked, for time-series |

**Auto-selection:** The model with the lowest RMSE on the held-out 20% test set is automatically saved as `aqi_model.pkl` and registered as the active production model.

**Metrics reported for each model:**
- MAE (Mean Absolute Error)
- MSE (Mean Squared Error)
- RMSE (Root Mean Squared Error)
- R² Score

**Features used (18 total):**

| Pollutants | Weather | Time-derived |
|---|---|---|
| PM2.5, PM10, NO₂, SO₂, CO, O₃, NH₃ | Temperature, Humidity, Wind Speed, Wind Direction, Pressure | Hour, Day of Week, Month, Year, Is Weekend, Season |

---

## 11. Explainable AI (XAI)

Every prediction is accompanied by an explanation generated by:

### SHAP (SHapley Additive exPlanations)
- **TreeExplainer** is used for tree-based models (XGBoost, LightGBM, Random Forest) — fast and exact.
- **KernelExplainer** is the fallback for other models — model-agnostic but slower.
- Returns: SHAP values per feature, base value, and a **waterfall bar chart** as a base64 PNG.
- Positive SHAP value = pollutant pushes AQI **higher** (red bar).
- Negative SHAP value = pollutant pushes AQI **lower** (blue bar).

### LIME (Local Interpretable Model-Agnostic Explanations)
- **TabularExplainer** fits a local linear model around the prediction instance.
- Returns: feature weights, predicted value, intercept, fidelity score, and a **horizontal bar chart**.
- Available via `POST /api/v1/predictions/explain` with `"methods": ["shap", "lime"]`.

---

## 12. User Roles & Permissions

| Feature | Citizen | Researcher | Policy Maker | Admin |
|---|---|---|---|---|
| AQI Prediction (single) | ✅ | ✅ | ✅ | ✅ |
| Batch Prediction | ✅ | ✅ | ✅ | ✅ |
| View Dashboard | ✅ | ✅ | ✅ | ✅ |
| Historical Data | ✅ | ✅ | ✅ | ✅ |
| Download Reports | ✅ | ✅ | ✅ | ✅ |
| Upload Datasets | ✅ | ✅ | ✅ | ✅ |
| OpenAQ API Fetch | — | ✅ | — | ✅ |
| View Analytics | ✅ | ✅ | ✅ | ✅ |
| ML Model Metrics | — | ✅ | ✅ | ✅ |
| Admin Panel | — | — | — | ✅ |
| Manage Users | — | — | — | ✅ |
| Activate ML Model | — | — | — | ✅ |
| View Audit Logs | — | — | — | ✅ |

**Creating an admin account** — after first registration, update the role directly in MySQL:
```sql
UPDATE users u
JOIN roles r ON r.name = 'admin'
SET u.role_id = r.id
WHERE u.email = 'your@email.com';
```

---

## 13. Running Tests

```bash
cd backend

# Activate virtual environment first
source .venv/bin/activate   # or .venv\Scripts\activate on Windows

# Run all tests with coverage
pytest

# Run only unit tests
pytest tests/unit/ -m unit

# Run only integration tests
pytest tests/integration/ -m integration

# Run with verbose output
pytest -v

# Generate HTML coverage report
pytest --cov=app --cov-report=html
# Open coverage_report/index.html in browser

# Run a specific test file
pytest tests/integration/test_auth_api.py -v
```

Coverage threshold is set to **70%** in `pytest.ini`. The CI pipeline fails if coverage drops below this.

---

## 14. Deployment

### GitHub Actions CI/CD

The workflow at `.github/workflows/ci.yml` runs on every push to `main`:

```
Push to main
    │
    ├── Backend tests (pytest)
    ├── Frontend lint (eslint)
    ├── Docker build validation
    └── Deploy to Render (on success)
```

---

## 15. Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Follow the existing code style (PEP 8 for Python, ESLint config for JS).
4. Write tests for any new service or API endpoint.
5. Ensure all tests pass: `pytest` and `npm run lint`
6. Submit a pull request with a clear description of the changes.

---

## AQI Health Scale Reference

| AQI Range | Category | Colour | Health Advisory |
|---|---|---|---|
| 0 – 50 | Good | 🟢 Green | Air quality is satisfactory |
| 51 – 100 | Moderate | 🟡 Yellow | Acceptable; sensitive individuals should limit prolonged outdoor exposure |
| 101 – 150 | Unhealthy for Sensitive Groups | 🟠 Orange | Sensitive groups may experience health effects |
| 151 – 200 | Unhealthy | 🔴 Red | Everyone may begin to experience health effects |
| 201 – 300 | Very Unhealthy | 🟣 Purple | Health alert — risk increased for everyone |
| 301 – 500 | Hazardous | 🔴 Maroon | Emergency conditions — serious risk for entire population |

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## Acknowledgements

- [OpenAQ](https://openaq.org) — open air quality data platform
- [US EPA AQI Calculator](https://www.airnow.gov/aqi/aqi-calculator/) — AQI breakpoint methodology
- [SHAP](https://github.com/slundberg/shap) — SHapley Additive exPlanations
- [LIME](https://github.com/marcotcr/lime) — Local Interpretable Model-Agnostic Explanations
- [XGBoost](https://xgboost.readthedocs.io) and [LightGBM](https://lightgbm.readthedocs.io) teams

---

*Built with ❤️ — AQI Prediction System © 2026*
@Mili
