# Developer Guide

## Project Layout

```
AI_AQI_Prediction_System/
├── backend/          Flask REST API (Python 3.11)
├── frontend/         React 18 + Vite SPA
├── ml/               ML training scripts and EDA notebooks
├── database/         SQL schema and seed files
├── docs/             This documentation folder
├── diagrams/         Architecture and UML diagrams
├── docker-compose.yml
└── README.md
```

## Local Development Setup

### 1. Clone and configure
```bash
git clone <repo-url>
cd AI_AQI_Prediction_System
cp backend/.env.example backend/.env
# Edit backend/.env — set SECRET_KEY, JWT_SECRET_KEY, DATABASE_URL
```

### 2. Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
flask db upgrade          # applies all migrations
flask seed-db             # seeds roles and default admin
flask run                 # starts on http://localhost:5000
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev               # starts on http://localhost:5173
```

### 4. Train ML models (required before predictions work)
```bash
cd ml/scripts
python train_models.py --no-lstm    # fast, no TensorFlow required
# or
python train_models.py              # includes LSTM (needs TensorFlow)
```

---

## Backend Architecture

### Application Factory (`app/__init__.py`)
Uses `create_app(config_name)` pattern. Supports `development`, `testing`, `production`.

### Layers
| Layer | Location | Responsibility |
|---|---|---|
| Routes | `app/api/v1/routes/` | HTTP — parse request, call service, return JSON |
| Services | `app/services/` | Business logic, DB writes, ML calls |
| Models | `app/models/` | SQLAlchemy ORM — maps to DB tables |
| Schemas | `app/schemas/` | Marshmallow input validation |
| ML | `app/ml/predictor.py` | Singleton model loader |
| XAI | `app/xai/explainer.py` | SHAP + LIME explanation generation |
| Utils | `app/utils/` | Shared helpers (audit, email, decorators) |

### Adding a new API endpoint
1. Create or add to a route file in `app/api/v1/routes/`
2. Add business logic to the matching service in `app/services/`
3. Add a Marshmallow schema in `app/schemas/` if accepting a request body
4. Register the blueprint in `app/api/v1/__init__.py` if it's a new blueprint
5. Add tests in `tests/integration/`

### Database migrations
```bash
flask db migrate -m "describe change"   # generate migration
flask db upgrade                         # apply
flask db downgrade                       # rollback one step
```

### Custom Flask CLI commands
```bash
flask seed-db          # insert roles + default admin user
flask create-admin     # interactive admin account creation
flask list-routes      # print all registered URL rules
```

---

## Frontend Architecture

### State management
- **Zustand** (`src/store/authStore.js`) — auth state only (user, tokens, isAuthenticated)
- Component-local `useState` for everything else
- Custom hooks (`src/hooks/`) encapsulate data-fetching logic

### Adding a new page
1. Create `src/pages/MyPage.jsx`
2. Add a lazy import in `src/App.jsx`
3. Add a `<Route>` inside the appropriate guard (`PrivateRoute`, `AdminRoute`, etc.)
4. Add a nav link in `src/components/common/Sidebar.jsx` if needed

### API calls
All HTTP calls go through `src/services/api.js` (Axios instance with JWT interceptors).
Domain services (`authService.js`, `predictionService.js`, etc.) wrap the Axios instance.

### Styling conventions
- Tailwind utility classes first
- Custom component classes defined in `src/styles/index.css` under `@layer components`
- Never use inline `style=` unless for dynamic values (colours, widths from data)

---

## ML Pipeline

### Training flow
```
raw CSV  →  clean_dataframe()  →  feature engineering
         →  train_test_split   →  6 models trained in parallel
         →  metrics compared   →  best model saved as aqi_model.pkl
```

### Adding a new model
1. Add a trainer function in `ml/scripts/train_models.py` following the `_lr`, `_rf` pattern
2. Append `("KEY", trainer_fn)` to the `trainers` list in `run()`
3. The auto-selection logic will pick the best by RMSE automatically

### Feature list
Defined in `FEATURE_COLS` in both `ml/scripts/train_models.py` and `backend/app/ml/predictor.py`.
Any change to this list requires retraining.

---

## Testing

```bash
cd backend
pytest                        # all tests
pytest tests/unit/            # unit tests only
pytest tests/integration/     # integration tests only
pytest -k "test_login"        # single test by name
pytest --cov=app --cov-report=html   # with coverage report
```

Coverage report opens at `backend/coverage_report/index.html`.

---

## Docker

```bash
docker compose up --build -d          # start all services
docker compose logs -f backend        # tail backend logs
docker exec aqi_backend flask db upgrade   # run migrations inside container
docker compose down                   # stop
docker compose down -v                # stop + wipe volumes
```

Add the `dev` profile for Adminer DB UI:
```bash
docker compose --profile dev up -d
# Adminer at http://localhost:8080
```
