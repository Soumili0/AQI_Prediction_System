@echo off
REM ============================================================
REM  AI AQI Prediction System — Windows Setup Script
REM  Run this once after cloning the repository.
REM ============================================================

echo.
echo ========================================
echo  AI AQI Prediction System — Setup
echo ========================================
echo.

REM ── Step 1: Backend Python environment ──────────────────────
echo [1/5] Setting up Python backend...
cd backend

if not exist .env (
    copy .env.example .env
    echo   Created backend\.env from .env.example
    echo   *** Edit backend\.env before continuing ***
)

python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt --quiet

echo   Backend dependencies installed.
cd ..

REM ── Step 2: Frontend Node environment ───────────────────────
echo.
echo [2/5] Setting up React frontend...
cd frontend
if not exist .env (
    copy .env.example .env
    echo   Created frontend\.env
)
call npm install --silent
echo   Frontend dependencies installed.
cd ..

REM ── Step 3: Train ML models ──────────────────────────────────
echo.
echo [3/5] Training ML models (no LSTM, fast mode)...
cd backend
call .venv\Scripts\activate.bat
cd ..\ml\scripts
python train_models.py --no-lstm
cd ..\..

REM ── Step 4: Database migrations ─────────────────────────────
echo.
echo [4/5] Running database migrations...
cd backend
call .venv\Scripts\activate.bat
set FLASK_APP=run.py
flask db upgrade
flask seed-db
cd ..

REM ── Step 5: Done ─────────────────────────────────────────────
echo.
echo [5/5] Setup complete!
echo.
echo  Start backend : cd backend ^&^& .venv\Scripts\activate ^&^& flask run
echo  Start frontend: cd frontend ^&^& npm run dev
echo  Docker (full) : docker compose up --build -d
echo.
pause
