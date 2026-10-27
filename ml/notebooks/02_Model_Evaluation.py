"""
Model Evaluation Notebook
===========================
Loads the trained best model and produces detailed evaluation plots:
  - Actual vs Predicted scatter
  - Residual plot + residual distribution histogram
  - Feature importance (for tree models)
  - Error analysis by AQI category
  - Inference latency benchmark (single + batch) with distribution plot
  - Cross-validation:
      * Standard shuffled KFold(5)   — overall stability check
      * TimeSeriesSplit(5)            — chronologically-honest CV

Run: python ml/notebooks/02_Model_Evaluation.py
"""

import os, sys, json, time, warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, KFold, TimeSeriesSplit

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


# ── Load model artefacts ──────────────────────────────────────────────────────

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


# ── Load evaluation dataset ───────────────────────────────────────────────────

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
    print(f"Evaluation set : {len(df):,} rows  |  {len(avail)} features")
    return X, y, avail


# ── Plot 1: Actual vs Predicted ───────────────────────────────────────────────

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


# ── Plot 2: Residual analysis ─────────────────────────────────────────────────

def plot_residuals(y_true, y_pred):
    residuals = y_true - y_pred
    fig, axes = plt.subplots(1, 2, figsize=(16, 5))

    # Residuals vs fitted
    axes[0].scatter(y_pred, residuals, alpha=0.3, s=15, color="#e76f51", edgecolors="none")
    axes[0].axhline(0, color="red", lw=1.5, linestyle="--")
    axes[0].set_xlabel("Predicted AQI")
    axes[0].set_ylabel("Residual (Actual − Predicted)")
    axes[0].set_title("Residuals vs Fitted Values")

    # Residual distribution histogram
    axes[1].hist(residuals, bins=50, color="#2d6a4f", edgecolor="white", alpha=0.85)
    axes[1].axvline(0, color="red", lw=1.5, linestyle="--")
    axes[1].set_xlabel("Residual")
    axes[1].set_ylabel("Count")
    axes[1].set_title(
        f"Residual Distribution  "
        f"(mean={residuals.mean():.2f}, std={residuals.std():.2f})"
    )

    plt.suptitle("Residual Analysis", fontsize=14, fontweight="bold")
    plt.tight_layout()
    _save("11_residual_analysis.png")

    # Print residual diagnostics
    print(f"\n  Residual diagnostics:")
    print(f"    Mean        : {residuals.mean():.4f}  (close to 0 = unbiased)")
    print(f"    Std dev     : {residuals.std():.4f}")
    print(f"    Max overest : {residuals.min():.2f}  (actual - predicted, most negative)")
    print(f"    Max underest: {residuals.max():.2f}  (actual - predicted, most positive)")
    pct_within_5  = (np.abs(residuals) <= 5).mean()  * 100
    pct_within_10 = (np.abs(residuals) <= 10).mean() * 100
    print(f"    Within ±5   : {pct_within_5:.1f}% of predictions")
    print(f"    Within ±10  : {pct_within_10:.1f}% of predictions")


# ── Plot 3: Feature importance ────────────────────────────────────────────────

def plot_feature_importance(model, feature_names):
    if not hasattr(model, "feature_importances_"):
        print("  Model has no feature_importances_ — skipping.")
        return

    imp = model.feature_importances_
    df  = pd.DataFrame({"feature": feature_names, "importance": imp})
    df  = df.sort_values("importance", ascending=True)

    fig, ax = plt.subplots(figsize=(10, max(7, len(feature_names) * 0.4)))
    colors = plt.cm.YlOrRd(np.linspace(0.3, 0.9, len(df)))
    ax.barh(df["feature"], df["importance"], color=colors, edgecolor="white")
    ax.set_xlabel("Feature Importance (Gini / Gain)")
    ax.set_title("Model Feature Importance", fontsize=13, fontweight="bold")
    for i, (val, _) in enumerate(zip(df["importance"], df["feature"])):
        ax.text(val + 0.001, i, f"{val:.4f}", va="center", fontsize=9)
    plt.tight_layout()
    _save("12_feature_importance.png")


# ── Plot 4: Error by AQI category ────────────────────────────────────────────

def plot_error_by_category(y_true, y_pred):
    ranges = [
        (0,   50,  "Good"),
        (51,  100, "Moderate"),
        (101, 150, "Sensitive"),
        (151, 200, "Unhealthy"),
        (201, 300, "Very Unhealthy"),
        (301, 500, "Hazardous"),
    ]
    results = []
    for lo, hi, cat in ranges:
        mask = (y_true >= lo) & (y_true <= hi)
        if mask.sum() < 5:
            continue
        mae = mean_absolute_error(y_true[mask], y_pred[mask])
        results.append({"category": cat, "count": int(mask.sum()), "mae": round(mae, 2)})

    if not results:
        return
    df = pd.DataFrame(results)
    colors = ["#00e400", "#ffff00", "#ff7e00", "#ff0000", "#8f3f97", "#7e0023"]

    fig, axes = plt.subplots(1, 2, figsize=(16, 5))
    axes[0].bar(df["category"], df["mae"], color=colors[:len(df)], edgecolor="white", alpha=0.9)
    axes[0].set_title("MAE by AQI Category")
    axes[0].set_xlabel("Category")
    axes[0].set_ylabel("Mean Absolute Error")
    axes[0].tick_params(axis="x", rotation=30)

    axes[1].bar(df["category"], df["count"], color=colors[:len(df)], edgecolor="white", alpha=0.9)
    axes[1].set_title("Sample Count by AQI Category")
    axes[1].tick_params(axis="x", rotation=30)

    plt.suptitle("Error Analysis by AQI Category", fontsize=13, fontweight="bold")
    plt.tight_layout()
    _save("13_error_by_category.png")


# ── Inference latency measurement ─────────────────────────────────────────────

def measure_inference_latency(model, scaler, feature_names,
                               n_runs: int = 200, batch_sizes: list = None):
    """
    Measures per-sample inference latency for single and batch predictions.

    Single-sample latency:
      - 10-run warm-up (CPU cache / JIT warm-up) not counted
      - n_runs timed measurements using time.perf_counter()
      - Reports: min, max, mean, median (p50), p95, p99, std, throughput

    Batch latency:
      - Measures scaling + prediction time for batch_sizes = [1, 10, 50, 100, 500]
      - Reports per-sample time and throughput for each batch size

    Generates:
      - 16_inference_latency.png — single-sample latency distribution + per-run line
      - 17_batch_latency_scaling.png — batch size vs throughput curve
    """
    if batch_sizes is None:
        batch_sizes = [1, 10, 50, 100, 500, 1000]

    # Build a representative single sample
    sample = np.zeros((1, len(feature_names)))

    # ── Single-sample latency ─────────────────────────────────────────────────
    print(f"\n  Warm-up (10 runs, not measured)…")
    for _ in range(10):
        scaler.transform(sample)
        model.predict(scaler.transform(sample))

    print(f"  Measuring single-sample latency ({n_runs} runs)…")
    latencies_ms = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        X_s = scaler.transform(sample)
        _   = model.predict(X_s)
        t1 = time.perf_counter()
        latencies_ms.append((t1 - t0) * 1000.0)

    lat = np.array(latencies_ms)
    mean_lat   = lat.mean()
    median_lat = np.percentile(lat, 50)
    p95_lat    = np.percentile(lat, 95)
    p99_lat    = np.percentile(lat, 99)

    print(f"\n{'='*55}")
    print(f"  Inference Latency Report — {type(model).__name__}")
    print(f"{'='*55}")
    print(f"  Runs          : {n_runs}")
    print(f"  Min           : {lat.min():.3f} ms")
    print(f"  Max           : {lat.max():.3f} ms")
    print(f"  Mean          : {mean_lat:.3f} ms")
    print(f"  Median (p50)  : {median_lat:.3f} ms")
    print(f"  p95           : {p95_lat:.3f} ms")
    print(f"  p99           : {p99_lat:.3f} ms")
    print(f"  Std dev       : {lat.std():.3f} ms")
    print(f"  Throughput    : {1000 / mean_lat:.0f} pred/sec (single-thread)")
    print(f"{'='*55}")

    # Plot 1: single-sample latency distribution + stability line
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].hist(lat, bins=30, color="#2d6a4f", edgecolor="white", alpha=0.85)
    axes[0].axvline(mean_lat,  color="#e74c3c", lw=2, linestyle="--",
                    label=f"Mean  = {mean_lat:.3f} ms")
    axes[0].axvline(p95_lat,   color="#e67e22", lw=2, linestyle=":",
                    label=f"p95   = {p95_lat:.3f} ms")
    axes[0].axvline(p99_lat,   color="#8e44ad", lw=1.5, linestyle="-.",
                    label=f"p99   = {p99_lat:.3f} ms")
    axes[0].set_xlabel("Latency (ms)")
    axes[0].set_ylabel("Count")
    axes[0].set_title("Single-Sample Latency Distribution", fontweight="bold")
    axes[0].legend()

    axes[1].plot(lat, color="#1e3a5f", alpha=0.6, linewidth=0.8)
    axes[1].axhline(mean_lat, color="#e74c3c", lw=1.5, linestyle="--",
                    label=f"Mean = {mean_lat:.3f} ms")
    axes[1].set_xlabel("Run Index")
    axes[1].set_ylabel("Latency (ms)")
    axes[1].set_title("Latency Per Run (Stability Check)", fontweight="bold")
    axes[1].legend()

    plt.suptitle(
        f"Inference Latency — {type(model).__name__}  ({n_runs} runs, post warm-up)",
        fontsize=13, fontweight="bold"
    )
    plt.tight_layout()
    _save("16_inference_latency.png")

    # ── Batch latency scaling ─────────────────────────────────────────────────
    print(f"\n  Measuring batch latency scaling across batch sizes: {batch_sizes}…")
    batch_results = []
    for bs in batch_sizes:
        X_batch = np.zeros((bs, len(feature_names)))
        timings = []
        for _ in range(20):  # 20 measurements per batch size
            t0  = time.perf_counter()
            Xs  = scaler.transform(X_batch)
            _   = model.predict(Xs)
            t1  = time.perf_counter()
            timings.append((t1 - t0) * 1000.0)
        total_ms      = np.mean(timings)
        per_sample_ms = total_ms / bs
        throughput    = bs / (total_ms / 1000.0)
        batch_results.append({
            "batch_size":     bs,
            "total_ms":       round(total_ms, 3),
            "per_sample_ms":  round(per_sample_ms, 4),
            "throughput":     round(throughput, 0),
        })
        print(f"    batch={bs:>5}  total={total_ms:7.2f} ms  "
              f"per_sample={per_sample_ms:.4f} ms  "
              f"throughput={throughput:,.0f} pred/sec")

    # Plot 2: batch size vs throughput
    df_batch = pd.DataFrame(batch_results)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].plot(df_batch["batch_size"], df_batch["throughput"],
                 marker="o", color="#2980b9", linewidth=2, markersize=7)
    axes[0].set_xlabel("Batch Size")
    axes[0].set_ylabel("Throughput (predictions/sec)")
    axes[0].set_title("Batch Size vs Throughput", fontweight="bold")
    axes[0].set_xscale("log")
    for _, row in df_batch.iterrows():
        axes[0].annotate(f"{int(row['throughput']):,}",
                         (row["batch_size"], row["throughput"]),
                         textcoords="offset points", xytext=(0, 8),
                         ha="center", fontsize=9)

    axes[1].plot(df_batch["batch_size"], df_batch["per_sample_ms"],
                 marker="s", color="#e74c3c", linewidth=2, markersize=7)
    axes[1].set_xlabel("Batch Size")
    axes[1].set_ylabel("Per-Sample Latency (ms)")
    axes[1].set_title("Batch Size vs Per-Sample Latency", fontweight="bold")
    axes[1].set_xscale("log")

    plt.suptitle(
        f"Batch Latency Scaling — {type(model).__name__}",
        fontsize=13, fontweight="bold"
    )
    plt.tight_layout()
    _save("17_batch_latency_scaling.png")

    return lat, batch_results


# ── Cross-validation (KFold + TimeSeriesSplit) ────────────────────────────────

def cross_validate_both(model, X, y, scaler):
    """
    Run two cross-validation strategies and compare them:

    1. KFold(5, shuffle=True)   — standard shuffled CV.
       Gives overall model stability but can leak future data into training.

    2. TimeSeriesSplit(5)        — chronologically honest CV.
       Each fold trains on earlier data and validates on later data.
       Reflects how the model will actually be used in production.
    """
    X_scaled = scaler.transform(X)

    # Strategy 1: Shuffled KFold
    print("\n  --- Cross-Validation: KFold(5, shuffle=True) ---")
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    kf_r2   = cross_val_score(model, X_scaled, y, cv=kf, scoring="r2",   n_jobs=-1)
    kf_rmse = -cross_val_score(model, X_scaled, y, cv=kf,
                               scoring="neg_root_mean_squared_error", n_jobs=-1)
    print(f"    R²   per fold : {kf_r2.round(4)}")
    print(f"    R²   mean±std : {kf_r2.mean():.4f} ± {kf_r2.std():.4f}")
    print(f"    RMSE per fold : {kf_rmse.round(4)}")
    print(f"    RMSE mean±std : {kf_rmse.mean():.4f} ± {kf_rmse.std():.4f}")

    # Strategy 2: TimeSeriesSplit
    print("\n  --- Cross-Validation: TimeSeriesSplit(5) ---")
    tscv = TimeSeriesSplit(n_splits=5)
    ts_r2   = cross_val_score(model, X_scaled, y, cv=tscv, scoring="r2",   n_jobs=-1)
    ts_rmse = -cross_val_score(model, X_scaled, y, cv=tscv,
                               scoring="neg_root_mean_squared_error", n_jobs=-1)
    print(f"    R²   per fold : {ts_r2.round(4)}")
    print(f"    R²   mean±std : {ts_r2.mean():.4f} ± {ts_r2.std():.4f}")
    print(f"    RMSE per fold : {ts_rmse.round(4)}")
    print(f"    RMSE mean±std : {ts_rmse.mean():.4f} ± {ts_rmse.std():.4f}")

    gap = kf_r2.mean() - ts_r2.mean()
    if gap > 0.01:
        print(f"\n  ⚠  KFold R² is {gap:.4f} higher than TimeSeriesSplit R².")
        print(f"     This gap suggests the model benefits from future data leakage")
        print(f"     in the shuffled CV — TimeSeriesSplit R² is more realistic.")
    else:
        print(f"\n  ✓  KFold and TimeSeriesSplit R² are close ({gap:.4f} gap).")
        print(f"     No significant temporal leakage detected.")

    # Comparison plot
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fold_labels = [f"Fold {i+1}" for i in range(5)]

    axes[0].plot(fold_labels, kf_r2, marker="o", label="KFold (shuffle)",
                 color="#2980b9", linewidth=2)
    axes[0].plot(fold_labels, ts_r2, marker="s", label="TimeSeriesSplit",
                 color="#e74c3c", linewidth=2)
    axes[0].axhline(kf_r2.mean(), color="#2980b9", lw=1, linestyle="--", alpha=0.6)
    axes[0].axhline(ts_r2.mean(), color="#e74c3c", lw=1, linestyle="--", alpha=0.6)
    axes[0].set_ylabel("R² Score")
    axes[0].set_title("R² per Fold: KFold vs TimeSeriesSplit", fontweight="bold")
    axes[0].legend()
    axes[0].set_ylim([min(ts_r2.min(), kf_r2.min()) - 0.01, 1.01])

    axes[1].plot(fold_labels, kf_rmse, marker="o", label="KFold (shuffle)",
                 color="#2980b9", linewidth=2)
    axes[1].plot(fold_labels, ts_rmse, marker="s", label="TimeSeriesSplit",
                 color="#e74c3c", linewidth=2)
    axes[1].set_ylabel("RMSE")
    axes[1].set_title("RMSE per Fold: KFold vs TimeSeriesSplit", fontweight="bold")
    axes[1].legend()

    plt.suptitle(
        f"Cross-Validation Comparison — {type(model).__name__}",
        fontsize=13, fontweight="bold"
    )
    plt.tight_layout()
    _save("18_cross_validation_comparison.png")

    return {
        "kfold_r2_mean":        round(float(kf_r2.mean()),   4),
        "kfold_r2_std":         round(float(kf_r2.std()),    4),
        "kfold_rmse_mean":      round(float(kf_rmse.mean()), 4),
        "timeseries_r2_mean":   round(float(ts_r2.mean()),   4),
        "timeseries_r2_std":    round(float(ts_r2.std()),    4),
        "timeseries_rmse_mean": round(float(ts_rmse.mean()), 4),
    }


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

    print("\nRunning cross-validation (KFold + TimeSeriesSplit)…")
    cv_results = cross_validate_both(model, X, y, scaler)

    print("\nMeasuring inference latency…")
    measure_inference_latency(model, scaler, avail, n_runs=200)

    # Save evaluation summary JSON
    summary = {
        "model":       model_name,
        "n_samples":   len(y),
        "n_features":  len(avail),
        "mae":         round(float(mean_absolute_error(y, y_pred)),              4),
        "rmse":        round(float(np.sqrt(mean_squared_error(y, y_pred))),      4),
        "r2":          round(float(r2_score(y, y_pred)),                         4),
        "cross_validation": cv_results,
    }
    summary_path = os.path.join(MODELS_DIR, "evaluation_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n  Evaluation summary → {summary_path}")

    print(f"\nAll evaluation plots saved → {REPORTS_DIR}")
    print("Model evaluation complete ✓")


if __name__ == "__main__":
    run()
