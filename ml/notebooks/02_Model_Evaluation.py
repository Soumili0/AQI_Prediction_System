"""
Model Evaluation Notebook
===========================
Loads the trained best model and produces detailed evaluation plots:
  - Actual vs Predicted scatter
  - Residual plot
  - Error distribution histogram
  - Feature importance (for tree models)
  - Learning curves
  - Cross-validation summary

Run: python ml/notebooks/02_Model_Evaluation.py
"""

import os, sys, json, warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, KFold

ROOT        = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODELS_DIR  = os.path.join(ROOT, "models")
REPORTS_DIR = os.path.join(ROOT, "reports")
DATA_PROC   = os.path.join(ROOT, "data", "processed")
DATA_RAW    = os.path.join(ROOT, "data", "raw")
os.makedirs(REPORTS_DIR, exist_ok=True)

sns.set_theme(style="whitegrid", font_scale=1.1)


def _save(name):
    p = os.path.join(REPORTS_DIR, name)
    plt.savefig(p, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  → {p}")


def load_artefacts():
    model_path    = os.path.join(MODELS_DIR, "aqi_model.pkl")
    scaler_path   = os.path.join(MODELS_DIR, "scaler.pkl")
    features_path = os.path.join(MODELS_DIR, "feature_names.json")

    if not os.path.exists(model_path):
        print("ERROR: aqi_model.pkl not found. Run train_models.py first.")
        sys.exit(1)

    model   = joblib.load(model_path)
    scaler  = joblib.load(scaler_path)
    with open(features_path) as f:
        features = json.load(f)

    print(f"Model loaded   : {type(model).__name__}")
    print(f"Features ({len(features)}): {features}")
    return model, scaler, features


def load_data(features):
    candidates = [
        os.path.join(DATA_PROC, "eda_cleaned.csv"),
        os.path.join(DATA_RAW,  "synthetic_aqi_data.csv"),
    ]
    path = next((p for p in candidates if os.path.exists(p)), None)
    if not path:
        print("ERROR: No dataset found. Run 01_EDA_AQI_Analysis.py first.")
        sys.exit(1)

    df = pd.read_csv(path)
    avail = [f for f in features if f in df.columns]
    df = df[avail + ["aqi"]].dropna()

    X = df[avail].values
    y = df["aqi"].values
    print(f"Evaluation set : {len(df):,} rows")
    return X, y, avail


# ── Plot 1: Actual vs Predicted ──────────────────────────────────────────────
def plot_actual_vs_predicted(y_true, y_pred):
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.scatter(y_true, y_pred, alpha=0.3, s=15, color="#1e3a5f", edgecolors="none")
    lim = [min(y_true.min(), y_pred.min()) - 5, max(y_true.max(), y_pred.max()) + 5]
    ax.plot(lim, lim, "r--", lw=1.5, label="Perfect prediction")
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("Actual AQI"); ax.set_ylabel("Predicted AQI")
    mae  = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2   = r2_score(y_true, y_pred)
    ax.set_title(f"Actual vs Predicted AQI\nMAE={mae:.2f}  RMSE={rmse:.2f}  R²={r2:.4f}",
                 fontsize=13, fontweight="bold")
    ax.legend()
    plt.tight_layout()
    _save("10_actual_vs_predicted.png")


# ── Plot 2: Residuals ────────────────────────────────────────────────────────
def plot_residuals(y_true, y_pred):
    residuals = y_true - y_pred
    fig, axes = plt.subplots(1, 2, figsize=(16, 5))

    # Residuals vs fitted
    axes[0].scatter(y_pred, residuals, alpha=0.3, s=15, color="#e76f51", edgecolors="none")
    axes[0].axhline(0, color="red", lw=1.5, linestyle="--")
    axes[0].set_xlabel("Predicted AQI"); axes[0].set_ylabel("Residual (Actual − Predicted)")
    axes[0].set_title("Residuals vs Fitted Values")

    # Residual histogram
    axes[1].hist(residuals, bins=50, color="#2d6a4f", edgecolor="white", alpha=0.85)
    axes[1].axvline(0, color="red", lw=1.5, linestyle="--")
    axes[1].set_xlabel("Residual"); axes[1].set_ylabel("Count")
    axes[1].set_title(f"Residual Distribution  (mean={residuals.mean():.2f}, std={residuals.std():.2f})")

    plt.suptitle("Residual Analysis", fontsize=14, fontweight="bold")
    plt.tight_layout()
    _save("11_residual_analysis.png")


# ── Plot 3: Feature importance (tree models) ─────────────────────────────────
def plot_feature_importance(model, feature_names):
    if not hasattr(model, "feature_importances_"):
        print("  Model has no feature_importances_ — skipping.")
        return

    imp = model.feature_importances_
    df  = pd.DataFrame({"feature": feature_names, "importance": imp})
    df  = df.sort_values("importance", ascending=True)

    fig, ax = plt.subplots(figsize=(10, 7))
    colors = plt.cm.YlOrRd(np.linspace(0.3, 0.9, len(df)))
    ax.barh(df["feature"], df["importance"], color=colors, edgecolor="white")
    ax.set_xlabel("Feature Importance (Gini / Gain)")
    ax.set_title("Model Feature Importance", fontsize=13, fontweight="bold")
    for i, (val, name) in enumerate(zip(df["importance"], df["feature"])):
        ax.text(val + 0.001, i, f"{val:.4f}", va="center", fontsize=9)
    plt.tight_layout()
    _save("12_feature_importance.png")


# ── Plot 4: Error by AQI range ────────────────────────────────────────────────
def plot_error_by_category(y_true, y_pred):
    ranges = [(0,50,"Good"),(51,100,"Moderate"),(101,150,"Sensitive"),
              (151,200,"Unhealthy"),(201,300,"Very Unhealthy"),(301,500,"Hazardous")]
    results = []
    for lo, hi, cat in ranges:
        mask = (y_true >= lo) & (y_true <= hi)
        if mask.sum() < 5: continue
        mae = mean_absolute_error(y_true[mask], y_pred[mask])
        results.append({"category": cat, "count": mask.sum(), "mae": round(mae, 2)})

    if not results: return
    df = pd.DataFrame(results)
    colors = ["#00e400","#ffff00","#ff7e00","#ff0000","#8f3f97","#7e0023"]

    fig, axes = plt.subplots(1, 2, figsize=(16, 5))
    axes[0].bar(df["category"], df["mae"], color=colors[:len(df)], edgecolor="white", alpha=0.9)
    axes[0].set_title("MAE by AQI Category"); axes[0].set_xlabel("Category")
    axes[0].set_ylabel("Mean Absolute Error"); axes[0].tick_params(axis="x", rotation=30)

    axes[1].bar(df["category"], df["count"], color=colors[:len(df)], edgecolor="white", alpha=0.9)
    axes[1].set_title("Sample Count by AQI Category"); axes[1].tick_params(axis="x", rotation=30)

    plt.suptitle("Error Analysis by AQI Category", fontsize=13, fontweight="bold")
    plt.tight_layout()
    _save("13_error_by_category.png")


# ── Cross-validation ──────────────────────────────────────────────────────────
def cross_validate(model, X, y, scaler):
    print("\nRunning 5-fold cross-validation…")
    X_scaled = scaler.transform(X)
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X_scaled, y, cv=kf, scoring="r2", n_jobs=-1)
    print(f"  CV R² scores: {cv_scores.round(4)}")
    print(f"  Mean R²: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    return cv_scores


# ── Print metrics summary ─────────────────────────────────────────────────────
def print_metrics(y_true, y_pred, model_name="Best Model"):
    mae  = mean_absolute_error(y_true, y_pred)
    mse  = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    r2   = r2_score(y_true, y_pred)
    print(f"\n{'='*50}")
    print(f" {model_name} — Evaluation Metrics")
    print(f"{'='*50}")
    print(f"  MAE  : {mae:.4f}")
    print(f"  MSE  : {mse:.4f}")
    print(f"  RMSE : {rmse:.4f}")
    print(f"  R²   : {r2:.4f}")
    print(f"{'='*50}")


# ── Main ──────────────────────────────────────────────────────────────────────
def run():
    print("\n" + "="*55)
    print("  AI AQI Prediction — Model Evaluation")
    print("="*55)

    model, scaler, features = load_artefacts()
    X, y, avail = load_data(features)
    X_scaled = scaler.transform(X)
    y_pred   = model.predict(X_scaled)
    model_name = type(model).__name__

    print_metrics(y, y_pred, model_name)

    print("\nGenerating evaluation plots…")
    plot_actual_vs_predicted(y, y_pred)
    plot_residuals(y, y_pred)
    plot_feature_importance(model, avail)
    plot_error_by_category(y, y_pred)
    cross_validate(model, X, y, scaler)

    print(f"\nAll evaluation plots saved → {REPORTS_DIR}")
    print("Model evaluation complete ✓")


if __name__ == "__main__":
    run()
