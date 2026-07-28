#!/usr/bin/env bash
# ============================================================
#  AI AQI Prediction System — Linux/macOS Setup Script
#  Run: chmod +x setup.sh && ./setup.sh
# ============================================================
set -e

echo ""
echo "========================================"
echo " AI AQI Prediction System — Setup"
echo "========================================"
echo ""

# ── Step 1: Backend ──────────────────────────────────────────
echo "[1/5] Setting up Python backend..."
cd backend

[ ! -f .env ] && cp .env.example .env && echo "  Created backend/.env — edit it before running!"

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -q
echo "  Backend dependencies installed."
cd ..

# ── Step 2: Frontend ─────────────────────────────────────────
echo ""
echo "[2/5] Setting up React frontend..."
cd frontend
[ ! -f .env ] && cp .env.example .env
npm install --silent
echo "  Frontend dependencies installed."
cd ..

# ── Step 3: ML Training ───────────────────────────────────────
echo ""
echo "[3/5] Training ML models (no LSTM, fast mode)..."
cd backend && source .venv/bin/activate && cd ..
cd ml/scripts
python3 train_models.py --no-lstm
cd ../..

# ── Step 4: Migrations + Seed ────────────────────────────────
echo ""
echo "[4/5] Running database migrations..."
cd backend
source .venv/bin/activate
FLASK_APP=run.py flask db upgrade
FLASK_APP=run.py flask seed-db
cd ..

# ── Done ─────────────────────────────────────────────────────
echo ""
echo "[5/5] Setup complete!"
echo ""
echo "  Start backend : cd backend && source .venv/bin/activate && flask run"
echo "  Start frontend: cd frontend && npm run dev"
echo "  Docker (full) : docker compose up --build -d"
echo ""
