"""
ML Training Pipeline — AQI Prediction
=======================================
Trains 6 models, compares metrics, auto-saves the best one.

Usage:
  python ml/scripts/train_models.py
  python ml/scripts/train_models.py --data path/to/data.csv --no-lstm
"""

import os, sys, json, time, argparse, warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

import xgboost as xgb
import lightgbm as lgb

ROOT        = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODELS_DIR  = os.path.join(ROOT, "models")
REPORTS_DIR = os.path.join(ROOT, "reports")
DATA_PROC   = os.path.join(ROOT, "data", "processed")
DATA_RAW    = os.path.join(ROOT, "data", "raw")
for d in [MODELS_DIR, REPORTS_DIR]:
    os.makedirs(d, exist_ok=True)

MODEL_PATH   = os.path.join(MODELS_DIR, "aqi_model.pkl")
SCALER_PATH  = os.path.join(MODELS_DIR, "scaler.pkl")
FEATURES_PATH= os.path.join(MODELS_DIR, "feature_names.json")
COMPARE_PATH = os.path.join(MODELS_DIR, "model_comparison.csv")

FEATURE_COLS = [
    "pm25","pm10","no2","so2","co","o3","nh3",
    "temperature","humidity","wind_speed","wind_direction","pressure",
    "hour","day_of_week","month","year","is_weekend","season",
]
TARGET = "aqi"


# ── Data preparation ──────────────────────────────────────────────────────────
def load_and_prepare(data_path):
    print(f"\nLoading: {data_path}")
    df = pd.read_csv(data_path)
    print(f"  Raw shape: {df.shape}")

    if "recorded_at" in df.columns:
        df["recorded_at"] = pd.to_datetime(df["recorded_at"], errors="coerce")
        if "hour"        not in df.columns: df["hour"]        = df["recorded_at"].dt.hour
        if "day_of_week" not in df.columns: df["day_of_week"] = df["recorded_at"].dt.dayofweek
        if "month"       not in df.columns: df["month"]       = df["recorded_at"].dt.month
        if "year"        not in df.columns: df["year"]        = df["recorded_at"].dt.year
        if "is_weekend"  not in df.columns: df["is_weekend"]  = df["day_of_week"].isin([5,6]).astype(int)
        if "season"      not in df.columns:
            df["season"] = df["month"].map(
                {12:0,1:0,2:0,3:1,4:1,5:1,6:2,7:2,8:2,9:3,10:3,11:3}
            )

    available = [c for c in FEATURE_COLS if c in df.columns]
    required  = [c for c in ["pm25","pm10","aqi"] if c not in df.columns]
    if required:
        raise ValueError(f"Required columns missing: {required}")

    df = df[available + [TARGET]].dropna()
    print(f"  After dropna: {df.shape}")
    if len(df) < 200:
        raise ValueError(f"Too few rows after cleaning: {len(df)} (need ≥ 200)")

    X = df[available].values
    y = df[TARGET].values
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    scaler   = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)
    print(f"  Train={len(X_train)}  Test={len(X_test)}  Features={len(available)}")
    return X_train_s, X_test_s, y_train, y_test, scaler, available


def _metrics(y_true, y_pred, name, elapsed):
    mae  = mean_absolute_error(y_true, y_pred)
    mse  = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    r2   = r2_score(y_true, y_pred)
    print(f"  {name:<30} MAE={mae:.3f}  RMSE={rmse:.3f}  R²={r2:.4f}  t={elapsed:.1f}s")
    return {"model":name,"mae":round(mae,4),"mse":round(mse,4),
            "rmse":round(rmse,4),"r2":round(r2,4),"train_time_s":round(elapsed,2)}


# ── Model trainers ────────────────────────────────────────────────────────────
def _lr(Xtr, ytr, Xts, yts):
    t=time.time(); m=LinearRegression(); m.fit(Xtr,ytr)
    return m, _metrics(yts, m.predict(Xts), "Linear Regression", time.time()-t)

def _dt(Xtr, ytr, Xts, yts):
    t=time.time()
    m=DecisionTreeRegressor(max_depth=12,min_samples_split=10,random_state=42)
    m.fit(Xtr,ytr)
    return m, _metrics(yts, m.predict(Xts), "Decision Tree", time.time()-t)

def _rf(Xtr, ytr, Xts, yts):
    t=time.time()
    m=RandomForestRegressor(n_estimators=200,n_jobs=-1,random_state=42)
    m.fit(Xtr,ytr)
    return m, _metrics(yts, m.predict(Xts), "Random Forest", time.time()-t)

def _xgb(Xtr, ytr, Xts, yts):
    t=time.time()
    m=xgb.XGBRegressor(n_estimators=500,learning_rate=0.05,max_depth=7,
                        subsample=0.8,colsample_bytree=0.8,
                        n_jobs=-1,random_state=42,verbosity=0)
    m.fit(Xtr,ytr,eval_set=[(Xts,yts)],verbose=False)
    return m, _metrics(yts, m.predict(Xts), "XGBoost", time.time()-t)

def _lgb(Xtr, ytr, Xts, yts):
    t=time.time()
    m=lgb.LGBMRegressor(n_estimators=500,learning_rate=0.05,num_leaves=64,
                         subsample=0.8,n_jobs=-1,random_state=42,verbosity=-1)
    m.fit(Xtr,ytr,eval_set=[(Xts,yts)],
          callbacks=[lgb.early_stopping(50,verbose=False),lgb.log_evaluation(-1)])
    return m, _metrics(yts, m.predict(Xts), "LightGBM", time.time()-t)

def _lstm(Xtr, ytr, Xts, yts):
    try:
        import tensorflow as tf
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
        from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
        from tensorflow.keras.optimizers import Adam
    except ImportError:
        print("  TensorFlow not found — skipping LSTM")
        return None, {"model":"LSTM","mae":None,"mse":None,"rmse":None,"r2":None,"train_time_s":0}

    t = time.time()
    Xtr3 = Xtr.reshape(Xtr.shape[0], 1, Xtr.shape[1])
    Xts3 = Xts.reshape(Xts.shape[0], 1, Xts.shape[1])
    n = Xtr.shape[1]

    model = Sequential([
        LSTM(128, return_sequences=True, input_shape=(1,n)),
        BatchNormalization(), Dropout(0.3),
        LSTM(64, return_sequences=False),
        BatchNormalization(), Dropout(0.2),
        Dense(32, activation="relu"), Dense(1),
    ])
    model.compile(optimizer=Adam(1e-3), loss="mse", metrics=["mae"])
    cbs = [EarlyStopping(patience=15, restore_best_weights=True),
           ReduceLROnPlateau(patience=7, factor=0.5, verbose=0)]
    model.fit(Xtr3, ytr, validation_data=(Xts3,yts),
              epochs=100, batch_size=64, callbacks=cbs, verbose=0)

    preds = model.predict(Xts3, verbose=0).flatten()
    m_dict = _metrics(yts, preds, "LSTM", time.time()-t)

    lstm_path = os.path.join(MODELS_DIR, "lstm_model")
    model.save(lstm_path)
    print(f"  LSTM model saved → {lstm_path}")
    return model, m_dict


# ── Comparison plot ───────────────────────────────────────────────────────────
def plot_comparison(results):
    df = pd.DataFrame([r for r in results if r["rmse"] is not None])
    if df.empty: return
    fig, axes = plt.subplots(1,3,figsize=(18,6))
    for ax,(metric,label,color) in zip(axes,[("mae","MAE","#e74c3c"),("rmse","RMSE","#e67e22"),("r2","R²","#27ae60")]):
        s = df.sort_values(metric, ascending=(metric!="r2"))
        bars = ax.barh(s["model"], s[metric], color=color, alpha=0.85, edgecolor="white")
        ax.set_title(f"Model Comparison — {label}", fontweight="bold")
        ax.set_xlabel(label)
        for b,v in zip(bars, s[metric]):
            ax.text(b.get_width()+max(s[metric])*0.01, b.get_y()+b.get_height()/2,
                    f"{v:.4f}", va="center", fontsize=9)
        ax.invert_yaxis()
    plt.suptitle("ML Model Performance Comparison", fontsize=15, fontweight="bold")
    plt.tight_layout()
    p = os.path.join(REPORTS_DIR, "model_comparison.png")
    plt.savefig(p, dpi=150, bbox_inches="tight"); plt.close()
    print(f"  Comparison plot → {p}")


# ── Main ──────────────────────────────────────────────────────────────────────
def run(data_path, include_lstm=True):
    print("\n" + "="*60)
    print("  AI AQI Prediction — Model Training Pipeline")
    print("="*60)

    Xtr, Xts, ytr, yts, scaler, features = load_and_prepare(data_path)

    trainers = [("LR",_lr),("DT",_dt),("RF",_rf),("XGB",_xgb),("LGB",_lgb)]
    if include_lstm: trainers.append(("LSTM",_lstm))

    trained, results = {}, []
    print("\n--- Training ---")
    for key, fn in trainers:
        print(f"\n{key}:")
        m, meta = fn(Xtr, ytr, Xts, yts)
        meta["train_size"] = len(Xtr)
        meta["test_size"]  = len(Xts)
        trained[key], results = m, results + [meta]

    # Save comparison
    pd.DataFrame(results).to_csv(COMPARE_PATH, index=False)
    print(f"\nComparison → {COMPARE_PATH}")
    print(pd.DataFrame(results)[["model","mae","rmse","r2"]].to_string(index=False))
    plot_comparison(results)

    # Best model (lowest RMSE, exclude LSTM)
    sklearn_r = [r for r in results if r["model"] != "LSTM" and r["rmse"] is not None]
    best_meta = min(sklearn_r, key=lambda r: r["rmse"])
    best_key  = {"Linear Regression":"LR","Decision Tree":"DT",
                 "Random Forest":"RF","XGBoost":"XGB","LightGBM":"LGB"}[best_meta["model"]]
    best_model = trained[best_key]

    print(f"\n{'='*60}")
    print(f"  BEST: {best_meta['model']}  RMSE={best_meta['rmse']:.4f}  R²={best_meta['r2']:.4f}")
    print(f"{'='*60}")

    joblib.dump(best_model, MODEL_PATH)
    joblib.dump(scaler,     SCALER_PATH)
    with open(FEATURES_PATH,"w") as f: json.dump(features, f, indent=2)

    meta_out = {**best_meta, "features": features,
                "algorithm": best_meta["model"].lower().replace(" ","_")}
    with open(os.path.join(MODELS_DIR,"best_model_meta.json"),"w") as f:
        json.dump(meta_out, f, indent=2)

    print(f"\nSaved:")
    print(f"  Model    → {MODEL_PATH}")
    print(f"  Scaler   → {SCALER_PATH}")
    print(f"  Features → {FEATURES_PATH}")
    print("\nTraining complete ✓")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data",    default=None)
    parser.add_argument("--no-lstm", action="store_true")
    args = parser.parse_args()

    if args.data:
        path = args.data
    else:
        candidates = [
            os.path.join(DATA_PROC, "eda_cleaned.csv"),
            os.path.join(DATA_RAW,  "synthetic_aqi_data.csv"),
        ]
        path = next((p for p in candidates if os.path.exists(p)), None)
        if not path:
            print("No data found. Running EDA to generate synthetic data…")
            eda = os.path.join(ROOT, "notebooks", "01_EDA_AQI_Analysis.py")
            import subprocess
            subprocess.run([sys.executable, eda], check=True)
            path = os.path.join(DATA_PROC, "eda_cleaned.csv")

    run(path, include_lstm=not args.no_lstm)
