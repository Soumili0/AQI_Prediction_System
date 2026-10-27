"""
ML Training Pipeline — AQI Prediction
=======================================
Trains 5 models (Linear Regression, Decision Tree, Random Forest,
XGBoost, LightGBM), compares metrics, auto-saves the best one.

NEW in this version:
  - Hybrid features: log-ratios, Shannon entropy, pollutant synergy, lag features
  - Chronological (time-sorted) train/test split instead of random shuffle
  - Hyperparameter tuning for XGBoost and LightGBM via RandomizedSearchCV
  - LSTM rebuilt as a proper time-series model with a configurable lookback window
  - LSTM is disabled by default — TensorFlow is not compatible with Python 3.13

Supported input formats: CSV or XLSX.

Real dataset columns (AIR_QUALITY_WITH _AQI.xlsx):
  Date, Time, pm25, pm10, no2, co, so2, o3,
  Temperature, Humidity, Wind, Rain, AQI, AQI_category, Dominant_Pollutant

Usage:
  python ml/scripts/train_models.py
  python ml/scripts/train_models.py --data path/to/data.csv
  python ml/scripts/train_models.py --data path/to/data.xlsx --tune
  python ml/scripts/train_models.py --data path/to/data.csv --lstm
  python ml/scripts/train_models.py --no-hybrid   # skip hybrid features
"""

import os, sys, json, time, argparse, warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from scipy.stats import entropy as scipy_entropy

from sklearn.model_selection import (
    train_test_split, RandomizedSearchCV, TimeSeriesSplit
)
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

import xgboost as xgb
import lightgbm as lgb

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT        = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROJ_ROOT   = os.path.abspath(os.path.join(ROOT, ".."))
MODELS_DIR  = os.path.join(ROOT, "models")
REPORTS_DIR = os.path.join(ROOT, "reports")
DATA_PROC   = os.path.join(ROOT, "data", "processed")
DATA_RAW    = os.path.join(ROOT, "data", "raw")
REAL_DATASET = os.path.join(PROJ_ROOT, "dataset", "AIR_QUALITY_WITH _AQI.xlsx")

for d in [MODELS_DIR, REPORTS_DIR]:
    os.makedirs(d, exist_ok=True)

MODEL_PATH    = os.path.join(MODELS_DIR, "aqi_model.pkl")
SCALER_PATH   = os.path.join(MODELS_DIR, "scaler.pkl")
FEATURES_PATH = os.path.join(MODELS_DIR, "feature_names.json")
COMPARE_PATH  = os.path.join(MODELS_DIR, "model_comparison.csv")

# ── Column aliases ─────────────────────────────────────────────────────────────
COLUMN_ALIASES = {
    # Real dataset
    "Temperature":        "temperature",
    "Wind":               "wind_speed",
    "Rain":               "rain",
    "AQI":                "aqi",
    "AQI_category":       "aqi_category",
    "Dominant_Pollutant": "dominant_pollutant",
    # Generic CSV variants
    "pm2.5": "pm25", "pm_2_5": "pm25", "pm2_5": "pm25",
    "pm_10": "pm10",
    "nitrogen_dioxide": "no2",
    "sulphur_dioxide": "so2", "sulfur_dioxide": "so2",
    "carbon_monoxide": "co",
    "ozone": "o3",
    "ammonia": "nh3",
    "temp": "temperature", "temp_c": "temperature",
    "rh": "humidity", "relative_humidity": "humidity",
    "Humidity": "humidity",
    "ws": "wind_speed",
    "wd": "wind_direction",
    "pres": "pressure", "atm_pressure": "pressure",
    "date": "recorded_at", "datetime": "recorded_at",
    "timestamp": "recorded_at",
}

# Base pollutant columns (before hybrid engineering)
BASE_POLLUTANTS = ["pm25", "pm10", "no2", "so2", "co", "o3", "nh3"]
BASE_WEATHER    = ["temperature", "humidity", "wind_speed", "wind_direction",
                   "pressure", "rain"]
TIME_FEATURES   = ["hour", "day_of_week", "month", "year", "is_weekend", "season"]

TARGET = "aqi"

# Lookback window for LSTM sequences
LSTM_LOOKBACK = 24  # use last 24 timesteps to predict AQI


# ── Hybrid feature engineering ────────────────────────────────────────────────

def add_hybrid_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add hybrid engineered features to the dataframe.

    1. Log-ratio features  — log(pollutant_A / pollutant_B + ε)
       Captures relative concentration relationships on a log scale.

    2. Shannon entropy     — entropy of the pollutant concentration distribution
       per row. High entropy = many pollutants contributing equally.

    3. Synergy features    — multiplicative interaction between pollutants.
       Captures nonlinear co-occurrence effects.

    4. Lag features        — previous-timestep values for key pollutants.
       Only added when the dataframe is sorted by time (recorded_at).
    """
    eps = 1e-6  # avoid log(0)

    # 1. Log-ratio features
    log_ratio_pairs = [
        ("pm25", "pm10"),
        ("no2",  "so2"),
        ("co",   "o3"),
        ("pm25", "no2"),
    ]
    for a, b in log_ratio_pairs:
        if a in df.columns and b in df.columns:
            col = f"log_ratio_{a}_{b}"
            df[col] = np.log((df[a] + eps) / (df[b] + eps))

    # 2. Shannon entropy across pollutants present in this dataset
    pollutant_cols = [c for c in BASE_POLLUTANTS if c in df.columns]
    if len(pollutant_cols) >= 2:
        raw = df[pollutant_cols].clip(lower=0).values + eps
        row_sums = raw.sum(axis=1, keepdims=True)
        probs    = raw / row_sums          # normalize each row to a probability dist
        df["pollutant_entropy"] = -np.sum(probs * np.log(probs + eps), axis=1)

    # 3. Synergy (multiplicative interaction) features
    synergy_pairs = [
        ("pm25", "humidity"),    # PM2.5 × humidity — humidity worsens particulate effect
        ("no2",  "temperature"), # NO2 × temperature — thermal NOx formation
        ("o3",   "temperature"), # O3 × temperature  — temperature drives ozone formation
        ("co",   "no2"),         # CO × NO2           — co-combustion synergy
    ]
    for a, b in synergy_pairs:
        if a in df.columns and b in df.columns:
            col = f"synergy_{a}_{b}"
            df[col] = (df[a] + eps) * (df[b] + eps)
            # Log-scale to avoid very large values
            df[col] = np.log(df[col])

    # 4. Lag features (only when data is time-ordered)
    lag_cols = ["pm25", "pm10", "no2", "aqi"] if "aqi" in df.columns else ["pm25", "pm10", "no2"]
    for col in lag_cols:
        if col in df.columns:
            df[f"{col}_lag1"] = df[col].shift(1)
            df[f"{col}_lag3"] = df[col].shift(3)

    # Fill NaNs introduced by lags with the column mean
    lag_feature_names = [c for c in df.columns if "_lag" in c]
    for c in lag_feature_names:
        df[c] = df[c].fillna(df[c].mean())

    return df


def get_all_feature_cols(df: pd.DataFrame) -> list:
    """Return all feature column names present in df, in a consistent order."""
    base = BASE_POLLUTANTS + BASE_WEATHER + TIME_FEATURES
    hybrid = sorted([
        c for c in df.columns
        if c.startswith("log_ratio_")
        or c == "pollutant_entropy"
        or c.startswith("synergy_")
        or c.endswith("_lag1")
        or c.endswith("_lag3")
    ])
    all_cols = base + hybrid
    return [c for c in all_cols if c in df.columns]


# ── Data preparation ───────────────────────────────────────────────────────────

def _build_recorded_at(df: pd.DataFrame) -> pd.DataFrame:
    """Combine Date + Time into a single recorded_at datetime column."""
    if "Date" in df.columns and "Time" in df.columns:
        df["recorded_at"] = pd.to_datetime(
            df["Date"].astype(str) + " " + df["Time"].astype(str),
            errors="coerce",
        )
        df.drop(columns=["Date", "Time"], inplace=True, errors="ignore")
    elif "recorded_at" not in df.columns:
        for col in ["date", "datetime", "timestamp"]:
            if col in df.columns:
                df["recorded_at"] = pd.to_datetime(df[col], errors="coerce")
                break
    return df


def load_and_prepare(data_path: str, add_hybrid: bool = True,
                     chronological: bool = True):
    """
    Load dataset, normalise columns, engineer features, split chronologically.

    Args:
        data_path:     Path to CSV or XLSX dataset.
        add_hybrid:    Whether to add hybrid engineered features.
        chronological: If True, split by time order (no shuffle).
                       If False, use random train/test split (legacy behaviour).

    Returns:
        X_train_s, X_test_s, y_train, y_test, scaler, feature_names,
        X_train_raw (unscaled, for LSTM sequence building)
    """
    print(f"\nLoading: {data_path}")
    ext = os.path.splitext(data_path)[1].lower()
    if ext in (".xlsx", ".xls"):
        df = pd.read_excel(data_path)
    else:
        df = pd.read_csv(data_path, low_memory=False)
    print(f"  Raw shape: {df.shape}")

    # Build recorded_at before column normalisation
    df = _build_recorded_at(df)

    # Normalise column names
    df.columns = [c.strip().replace(" ", "_").replace("-", "_") for c in df.columns]
    df.rename(columns=COLUMN_ALIASES, inplace=True)

    # Verify target exists
    if TARGET not in df.columns:
        raise ValueError(
            f"Target column '{TARGET}' not found. "
            f"Available columns: {list(df.columns)}"
        )

    # Engineer time features from recorded_at
    if "recorded_at" in df.columns:
        df["recorded_at"] = pd.to_datetime(df["recorded_at"], errors="coerce")
        if "hour"        not in df.columns:
            df["hour"]        = df["recorded_at"].dt.hour
        if "day_of_week" not in df.columns:
            df["day_of_week"] = df["recorded_at"].dt.dayofweek
        if "month"       not in df.columns:
            df["month"]       = df["recorded_at"].dt.month
        if "year"        not in df.columns:
            df["year"]        = df["recorded_at"].dt.year
        if "is_weekend"  not in df.columns:
            df["is_weekend"]  = df["day_of_week"].isin([5, 6]).astype(int)
        if "season"      not in df.columns:
            df["season"] = df["month"].map(
                {12: 0, 1: 0, 2: 0, 3: 1, 4: 1, 5: 1,
                  6: 2, 7: 2, 8: 2, 9: 3, 10: 3, 11: 3}
            )

    # Sort chronologically before hybrid feature engineering
    # (lag features need time order to be meaningful)
    if "recorded_at" in df.columns:
        df = df.sort_values("recorded_at").reset_index(drop=True)
        print(f"  Sorted chronologically by recorded_at.")

    # Add hybrid features
    if add_hybrid:
        df = add_hybrid_features(df)
        print(f"  Hybrid features added.")

    # Select available feature columns
    available = get_all_feature_cols(df)

    # Check minimum required pollutants
    required = [c for c in ["pm25", "pm10"] if c not in df.columns]
    if required:
        raise ValueError(f"Required pollutant columns missing: {required}")

    df = df[available + [TARGET]].dropna()
    print(f"  After dropna: {df.shape}")

    if len(df) < 200:
        raise ValueError(
            f"Too few rows after cleaning: {len(df)} (need ≥ 200)"
        )

    X = df[available].values
    y = df[TARGET].values

    # ── Chronological split ────────────────────────────────────────────────────
    # Data is already time-sorted. Take last 20% as test set.
    # This is realistic: the model is trained on historical data
    # and tested on future (unseen) data — no data leakage.
    if chronological:
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        print(f"  Chronological split: train={len(X_train)}  test={len(X_test)}")
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        print(f"  Random split: train={len(X_train)}  test={len(X_test)}")

    scaler    = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    print(f"  Features ({len(available)}): {available}")
    return X_train_s, X_test_s, y_train, y_test, scaler, available, X_train


def _metrics(y_true, y_pred, name, elapsed):
    mae  = mean_absolute_error(y_true, y_pred)
    mse  = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    r2   = r2_score(y_true, y_pred)
    print(f"  {name:<35} MAE={mae:.3f}  RMSE={rmse:.3f}  R²={r2:.4f}  t={elapsed:.1f}s")
    return {
        "model": name, "mae": round(mae, 4), "mse": round(mse, 4),
        "rmse": round(rmse, 4), "r2": round(r2, 4),
        "train_time_s": round(elapsed, 2),
    }


# ── Model trainers ─────────────────────────────────────────────────────────────

def _lr(Xtr, ytr, Xts, yts):
    t = time.time()
    m = LinearRegression()
    m.fit(Xtr, ytr)
    return m, _metrics(yts, m.predict(Xts), "Linear Regression", time.time() - t)


def _dt(Xtr, ytr, Xts, yts):
    t = time.time()
    m = DecisionTreeRegressor(max_depth=12, min_samples_split=10, random_state=42)
    m.fit(Xtr, ytr)
    return m, _metrics(yts, m.predict(Xts), "Decision Tree", time.time() - t)


def _rf(Xtr, ytr, Xts, yts):
    t = time.time()
    m = RandomForestRegressor(n_estimators=200, n_jobs=-1, random_state=42)
    m.fit(Xtr, ytr)
    return m, _metrics(yts, m.predict(Xts), "Random Forest", time.time() - t)


def _xgb(Xtr, ytr, Xts, yts, tune: bool = False):
    """
    Train XGBoost. When tune=True, runs RandomizedSearchCV with
    TimeSeriesSplit(5) to find the best hyperparameters.
    TimeSeriesSplit ensures the CV respects chronological order —
    each fold trains on past data and validates on future data.
    """
    t = time.time()

    if tune:
        print("    [XGBoost] Running RandomizedSearchCV with TimeSeriesSplit(5)…")
        param_dist = {
            "n_estimators":    [200, 300, 500, 700],
            "learning_rate":   [0.01, 0.03, 0.05, 0.1],
            "max_depth":       [4, 5, 6, 7, 8],
            "subsample":       [0.6, 0.7, 0.8, 0.9],
            "colsample_bytree":[0.6, 0.7, 0.8, 0.9, 1.0],
            "min_child_weight":[1, 3, 5],
            "gamma":           [0, 0.1, 0.2, 0.5],
            "reg_alpha":       [0, 0.01, 0.1],
            "reg_lambda":      [1, 1.5, 2],
        }
        base_xgb = xgb.XGBRegressor(
            n_jobs=-1, random_state=42, verbosity=0, early_stopping_rounds=50,
        )
        tscv = TimeSeriesSplit(n_splits=5)
        search = RandomizedSearchCV(
            base_xgb, param_dist,
            n_iter=30,           # evaluate 30 random combinations
            cv=tscv,
            scoring="neg_root_mean_squared_error",
            n_jobs=-1,
            random_state=42,
            verbose=0,
        )
        search.fit(Xtr, ytr, eval_set=[(Xts, yts)])
        m = search.best_estimator_
        print(f"    Best XGB params: {search.best_params_}")
        # Save best params for reference
        with open(os.path.join(MODELS_DIR, "xgb_best_params.json"), "w") as f:
            json.dump(search.best_params_, f, indent=2)
    else:
        m = xgb.XGBRegressor(
            n_estimators=500, learning_rate=0.05, max_depth=7,
            subsample=0.8, colsample_bytree=0.8,
            n_jobs=-1, random_state=42, verbosity=0,
        )
        m.fit(Xtr, ytr, eval_set=[(Xts, yts)], verbose=False)

    return m, _metrics(yts, m.predict(Xts), "XGBoost", time.time() - t)


def _lgb(Xtr, ytr, Xts, yts, tune: bool = False):
    """
    Train LightGBM. When tune=True, runs RandomizedSearchCV with
    TimeSeriesSplit(5) to find the best hyperparameters.
    """
    t = time.time()

    if tune:
        print("    [LightGBM] Running RandomizedSearchCV with TimeSeriesSplit(5)…")
        param_dist = {
            "n_estimators":   [200, 300, 500, 700],
            "learning_rate":  [0.01, 0.03, 0.05, 0.1],
            "num_leaves":     [31, 50, 64, 80, 100, 128],
            "max_depth":      [-1, 5, 7, 9],
            "subsample":      [0.6, 0.7, 0.8, 0.9],
            "colsample_bytree":[0.6, 0.7, 0.8, 0.9, 1.0],
            "min_child_samples":[10, 20, 30, 50],
            "reg_alpha":      [0, 0.01, 0.1],
            "reg_lambda":     [0, 0.01, 0.1],
        }
        base_lgb = lgb.LGBMRegressor(n_jobs=-1, random_state=42, verbosity=-1)
        tscv = TimeSeriesSplit(n_splits=5)
        search = RandomizedSearchCV(
            base_lgb, param_dist,
            n_iter=30,
            cv=tscv,
            scoring="neg_root_mean_squared_error",
            n_jobs=-1,
            random_state=42,
            verbose=0,
        )
        search.fit(Xtr, ytr)
        m = search.best_estimator_
        print(f"    Best LGB params: {search.best_params_}")
        with open(os.path.join(MODELS_DIR, "lgb_best_params.json"), "w") as f:
            json.dump(search.best_params_, f, indent=2)
    else:
        m = lgb.LGBMRegressor(
            n_estimators=500, learning_rate=0.05, num_leaves=64,
            subsample=0.8, n_jobs=-1, random_state=42, verbosity=-1,
        )
        m.fit(
            Xtr, ytr,
            eval_set=[(Xts, yts)],
            callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(-1)],
        )

    return m, _metrics(yts, m.predict(Xts), "LightGBM", time.time() - t)


def _lstm(X_train_raw, y_train, X_test_raw, y_test, scaler, lookback: int = LSTM_LOOKBACK):
    """
    Proper time-series LSTM with a sliding lookback window.

    Unlike the previous single-timestep version, this builds sequences:
      - Each sample is a window of `lookback` consecutive timesteps
      - Shape: (n_samples, lookback, n_features)
      - Predicts the AQI at the next timestep after the window

    This is a true sequence model — it learns temporal patterns
    across `lookback` hours of pollutant history.

    Will silently skip if TensorFlow is not installed (Python 3.13).
    """
    try:
        import tensorflow as tf
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
        from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
        from tensorflow.keras.optimizers import Adam
    except ImportError:
        print("  TensorFlow not available (Python 3.13 incompatible) — skipping LSTM")
        return None, {
            "model": "LSTM", "mae": None, "mse": None,
            "rmse": None, "r2": None, "train_time_s": 0,
        }

    t = time.time()
    print(f"  Building LSTM sequences with lookback={lookback}…")

    # Scale the raw (unscaled) training data to build sequences
    X_train_s = scaler.transform(X_train_raw)
    X_test_s  = scaler.transform(X_test_raw)

    # Combine train and test for sequence building, then re-split
    # We need to build sequences across the boundary carefully.
    # Strategy: build sequences from train only; build test sequences
    # using the tail of train as context for the first test windows.
    all_X = np.vstack([X_train_s, X_test_s])
    all_y = np.concatenate([y_train, y_test])

    n_train = len(X_train_s)
    n_total = len(all_X)
    n_features = all_X.shape[1]

    def build_sequences(X_data, y_data, start, end):
        Xs, ys = [], []
        for i in range(start, end):
            if i < lookback:
                continue
            Xs.append(X_data[i - lookback:i])
            ys.append(y_data[i])
        return np.array(Xs), np.array(ys)

    X_seq_train, y_seq_train = build_sequences(all_X, all_y, lookback, n_train)
    X_seq_test,  y_seq_test  = build_sequences(all_X, all_y, n_train, n_total)

    if len(X_seq_train) < 100 or len(X_seq_test) < 10:
        print(f"  Not enough sequences after lookback={lookback} — skipping LSTM")
        return None, {
            "model": "LSTM", "mae": None, "mse": None,
            "rmse": None, "r2": None, "train_time_s": 0,
        }

    print(f"  LSTM train sequences: {X_seq_train.shape}  test: {X_seq_test.shape}")

    model = Sequential([
        LSTM(128, return_sequences=True, input_shape=(lookback, n_features)),
        BatchNormalization(),
        Dropout(0.3),
        LSTM(64, return_sequences=False),
        BatchNormalization(),
        Dropout(0.2),
        Dense(32, activation="relu"),
        Dense(1),
    ])
    model.compile(optimizer=Adam(1e-3), loss="mse", metrics=["mae"])

    cbs = [
        EarlyStopping(patience=15, restore_best_weights=True, monitor="val_loss"),
        ReduceLROnPlateau(patience=7, factor=0.5, verbose=0, monitor="val_loss"),
    ]

    model.fit(
        X_seq_train, y_seq_train,
        validation_data=(X_seq_test, y_seq_test),
        epochs=100, batch_size=64, callbacks=cbs, verbose=0,
    )

    preds = model.predict(X_seq_test, verbose=0).flatten()
    m_dict = _metrics(y_seq_test, preds, "LSTM", time.time() - t)

    lstm_path = os.path.join(MODELS_DIR, "lstm_model")
    model.save(lstm_path)
    print(f"  LSTM model saved → {lstm_path}")

    return model, m_dict


# ── Comparison plot ────────────────────────────────────────────────────────────
def plot_comparison(results):
    df = pd.DataFrame([r for r in results if r["rmse"] is not None])
    if df.empty:
        return
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    for ax, (metric, label, color) in zip(
        axes,
        [("mae", "MAE", "#e74c3c"), ("rmse", "RMSE", "#e67e22"), ("r2", "R²", "#27ae60")],
    ):
        s    = df.sort_values(metric, ascending=(metric != "r2"))
        bars = ax.barh(s["model"], s[metric], color=color, alpha=0.85, edgecolor="white")
        ax.set_title(f"Model Comparison — {label}", fontweight="bold")
        ax.set_xlabel(label)
        for b, v in zip(bars, s[metric]):
            ax.text(
                b.get_width() + max(s[metric]) * 0.01,
                b.get_y() + b.get_height() / 2,
                f"{v:.4f}", va="center", fontsize=9,
            )
        ax.invert_yaxis()
    plt.suptitle("ML Model Performance Comparison", fontsize=15, fontweight="bold")
    plt.tight_layout()
    p = os.path.join(REPORTS_DIR, "model_comparison.png")
    plt.savefig(p, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Comparison plot → {p}")


# ── Main ───────────────────────────────────────────────────────────────────────
def run(data_path: str, include_lstm: bool = False, tune: bool = False,
        add_hybrid: bool = True, chronological: bool = True,
        lstm_lookback: int = LSTM_LOOKBACK):

    print("\n" + "=" * 60)
    print("  AI AQI Prediction — Model Training Pipeline")
    print(f"  Hybrid features : {'ON' if add_hybrid else 'OFF'}")
    print(f"  Chrono split    : {'ON' if chronological else 'random'}")
    print(f"  Hyperparam tune : {'ON (RandomizedSearchCV + TimeSeriesSplit)' if tune else 'OFF (fixed hyperparams)'}")
    print(f"  LSTM            : {'ON (lookback=' + str(LSTM_LOOKBACK) + ')' if include_lstm else 'OFF'}")
    print("=" * 60)

    result = load_and_prepare(
        data_path,
        add_hybrid=add_hybrid,
        chronological=chronological,
    )
    Xtr, Xts, ytr, yts, scaler, features, X_train_raw = result

    trainers = [
        ("LR",  lambda: _lr(Xtr, ytr, Xts, yts)),
        ("DT",  lambda: _dt(Xtr, ytr, Xts, yts)),
        ("RF",  lambda: _rf(Xtr, ytr, Xts, yts)),
        ("XGB", lambda: _xgb(Xtr, ytr, Xts, yts, tune=tune)),
        ("LGB", lambda: _lgb(Xtr, ytr, Xts, yts, tune=tune)),
    ]

    trained, results = {}, []
    print("\n--- Training ---")
    for key, fn in trainers:
        print(f"\n{key}:")
        m, meta = fn()
        meta["train_size"] = len(Xtr)
        meta["test_size"]  = len(Xts)
        meta["split_type"] = "chronological" if chronological else "random"
        meta["hybrid_features"] = add_hybrid
        meta["tuned"] = tune if key in ("XGB", "LGB") else False
        trained[key] = m
        results.append(meta)

    # LSTM — needs raw unscaled data for proper sequence building
    if include_lstm:
        print("\nLSTM:")
        # Recover unscaled test data via inverse transform for sequence building
        X_test_raw = scaler.inverse_transform(Xts)
        m_lstm, meta_lstm = _lstm(X_train_raw, ytr, X_test_raw, yts, scaler,
                                  lookback=lstm_lookback)
        if m_lstm is not None:
            meta_lstm["train_size"] = len(Xtr)
            meta_lstm["test_size"]  = len(Xts)
            meta_lstm["split_type"] = "chronological"
            meta_lstm["hybrid_features"] = add_hybrid
            meta_lstm["tuned"] = False
            trained["LSTM"] = m_lstm
        results.append(meta_lstm)

    # Save comparison table
    pd.DataFrame(results).to_csv(COMPARE_PATH, index=False)
    print(f"\nComparison → {COMPARE_PATH}")
    print(pd.DataFrame(results)[["model", "mae", "rmse", "r2"]].to_string(index=False))
    plot_comparison(results)

    # Pick best model by lowest RMSE (sklearn models only, exclude LSTM)
    sklearn_results = [
        r for r in results
        if r["model"] != "LSTM" and r["rmse"] is not None
    ]
    best_meta = min(sklearn_results, key=lambda r: r["rmse"])
    key_map   = {
        "Linear Regression": "LR",
        "Decision Tree":     "DT",
        "Random Forest":     "RF",
        "XGBoost":           "XGB",
        "LightGBM":          "LGB",
    }
    best_key   = key_map[best_meta["model"]]
    best_model = trained[best_key]

    print(f"\n{'=' * 60}")
    print(f"  BEST: {best_meta['model']}"
          f"  RMSE={best_meta['rmse']:.4f}  R²={best_meta['r2']:.4f}")
    print(f"{'=' * 60}")

    # Persist model artefacts
    joblib.dump(best_model, MODEL_PATH)
    joblib.dump(scaler,     SCALER_PATH)
    with open(FEATURES_PATH, "w") as f:
        json.dump(features, f, indent=2)

    meta_out = {
        **best_meta,
        "features":        features,
        "algorithm":       best_meta["model"].lower().replace(" ", "_"),
        "hybrid_features": add_hybrid,
        "split_type":      "chronological" if chronological else "random",
        "tuned":           tune,
        "lstm_lookback":   lstm_lookback if include_lstm else None,
    }
    with open(os.path.join(MODELS_DIR, "best_model_meta.json"), "w") as f:
        json.dump(meta_out, f, indent=2)

    print(f"\nSaved:")
    print(f"  Model    → {MODEL_PATH}")
    print(f"  Scaler   → {SCALER_PATH}")
    print(f"  Features → {FEATURES_PATH}")
    print("\nTraining complete ✓")


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AQI Model Training Pipeline")
    parser.add_argument("--data",       default=None,
                        help="Path to CSV or XLSX dataset")
    parser.add_argument("--lstm",       action="store_true",
                        help="Include LSTM training with lookback window (requires TensorFlow / Python 3.11)")
    parser.add_argument("--tune",       action="store_true",
                        help="Run RandomizedSearchCV + TimeSeriesSplit hyperparameter tuning for XGBoost and LightGBM")
    parser.add_argument("--no-hybrid",  action="store_true",
                        help="Disable hybrid feature engineering (log-ratios, entropy, synergy, lags)")
    parser.add_argument("--no-chrono",  action="store_true",
                        help="Use random train/test split instead of chronological split")
    parser.add_argument("--lookback",   type=int, default=LSTM_LOOKBACK,
                        help=f"LSTM lookback window size (default: {LSTM_LOOKBACK})")
    args = parser.parse_args()

    if args.data:
        path = args.data
    else:
        candidates = [
            REAL_DATASET,
            os.path.join(DATA_PROC, "eda_cleaned.csv"),
            os.path.join(DATA_RAW,  "synthetic_aqi_data.csv"),
        ]
        path = next((p for p in candidates if os.path.exists(p)), None)

        if path is None:
            print("No dataset found. Running EDA to generate data first…")
            eda = os.path.join(ROOT, "notebooks", "01_EDA_AQI_Analysis.py")
            import subprocess
            subprocess.run([sys.executable, eda], check=True)
            path = os.path.join(DATA_PROC, "eda_cleaned.csv")

    print(f"Dataset: {path}")
    run(
        path,
        include_lstm=args.lstm,
        tune=args.tune,
        add_hybrid=not args.no_hybrid,
        chronological=not args.no_chrono,
        lstm_lookback=args.lookback,
    )
