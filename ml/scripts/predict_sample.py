"""
Sample Prediction Script
=========================
Demonstrates how to load the trained model and make predictions
without the Flask API. Useful for testing and batch offline jobs.

Inference latency is measured and reported for every prediction:
  - Single prediction: wall-clock time in milliseconds
  - Batch prediction: total time, per-sample time, and throughput (samples/sec)
  - A latency distribution plot is saved to ml/reports/

Usage:
  python ml/scripts/predict_sample.py
  python ml/scripts/predict_sample.py --city Delhi --pm25 120 --pm10 200
  python ml/scripts/predict_sample.py --latency-runs 200
"""

import os, sys, json, argparse, time
import numpy as np
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime, timezone

ROOT        = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODELS_DIR  = os.path.join(ROOT, "models")
REPORTS_DIR = os.path.join(ROOT, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

AQI_CATEGORIES = [
    (0,   50,  "Good",                           "Air quality is satisfactory."),
    (51,  100, "Moderate",                       "Acceptable quality; sensitive individuals should take precautions."),
    (101, 150, "Unhealthy for Sensitive Groups",  "Sensitive groups may experience health effects."),
    (151, 200, "Unhealthy",                      "Everyone may begin to experience health effects."),
    (201, 300, "Very Unhealthy",                 "Health alert: risk is increased for everyone."),
    (301, 500, "Hazardous",                      "Emergency conditions — serious risk."),
]

FEATURE_COLS = [
    "pm25","pm10","no2","so2","co","o3","nh3",
    "temperature","humidity","wind_speed","wind_direction","pressure",
    "hour","day_of_week","month","year","is_weekend","season",
]


def load_model():
    model_path    = os.path.join(MODELS_DIR, "aqi_model.pkl")
    scaler_path   = os.path.join(MODELS_DIR, "scaler.pkl")
    features_path = os.path.join(MODELS_DIR, "feature_names.json")

    if not os.path.exists(model_path):
        print("ERROR: aqi_model.pkl not found.")
        print("Run: python ml/scripts/train_models.py first.")
        sys.exit(1)

    model   = joblib.load(model_path)
    scaler  = joblib.load(scaler_path)
    with open(features_path) as f:
        features = json.load(f)
    return model, scaler, features


def get_aqi_info(value):
    for lo, hi, cat, advisory in AQI_CATEGORIES:
        if lo <= value <= hi:
            return cat, advisory
    return "Hazardous", "Emergency conditions."


def predict(features_dict, model, scaler, feature_names):
    """Make a single prediction. Returns (aqi, latency_ms)."""
    now = datetime.now(timezone.utc)
    defaults = {
        "hour":        now.hour,
        "day_of_week": now.weekday(),
        "month":       now.month,
        "year":        now.year,
        "is_weekend":  int(now.weekday() in (5, 6)),
        "season":      {12:0,1:0,2:0,3:1,4:1,5:1,6:2,7:2,8:2,9:3,10:3,11:3}[now.month],
        "nh3":         0.0, "temperature": 25.0, "humidity": 60.0,
        "wind_speed":  3.0, "wind_direction": 180.0, "pressure": 1013.0,
    }
    for k, v in defaults.items():
        features_dict.setdefault(k, v)

    vector = np.array([[float(features_dict.get(f, 0) or 0) for f in feature_names]])

    # ── Inference latency measurement ─────────────────────────────────────────
    # Use time.perf_counter() — higher resolution than time.time() on Windows.
    # We measure only the model inference path (scale + predict), not I/O.
    t_start = time.perf_counter()
    scaled  = scaler.transform(vector)
    aqi_raw = model.predict(scaled)[0]
    t_end   = time.perf_counter()

    latency_ms = (t_end - t_start) * 1000.0  # convert seconds → milliseconds
    aqi        = max(0.0, round(float(aqi_raw), 2))

    return aqi, latency_ms


def predict_batch(records: list, model, scaler, feature_names):
    """
    Predict AQI for a batch of records.
    Returns (aqi_list, total_ms, per_sample_ms, throughput_per_sec).
    """
    now = datetime.now(timezone.utc)
    defaults = {
        "hour":        now.hour,
        "day_of_week": now.weekday(),
        "month":       now.month,
        "year":        now.year,
        "is_weekend":  int(now.weekday() in (5, 6)),
        "season":      {12:0,1:0,2:0,3:1,4:1,5:1,6:2,7:2,8:2,9:3,10:3,11:3}[now.month],
        "nh3":         0.0, "temperature": 25.0, "humidity": 60.0,
        "wind_speed":  3.0, "wind_direction": 180.0, "pressure": 1013.0,
    }

    vectors = []
    for rec in records:
        row = dict(defaults)
        row.update(rec)
        vectors.append([float(row.get(f, 0) or 0) for f in feature_names])

    X = np.array(vectors)

    t_start = time.perf_counter()
    X_scaled = scaler.transform(X)
    preds    = model.predict(X_scaled)
    t_end    = time.perf_counter()

    total_ms      = (t_end - t_start) * 1000.0
    per_sample_ms = total_ms / len(records)
    throughput    = len(records) / (t_end - t_start)  # samples per second

    aqi_list = [max(0.0, round(float(p), 2)) for p in preds]
    return aqi_list, total_ms, per_sample_ms, throughput


def run_latency_benchmark(model, scaler, feature_names, n_runs: int = 100):
    """
    Run n_runs single-sample predictions and collect latency statistics.
    Generates a latency distribution plot saved to ml/reports/.

    The first few runs are typically slower (cold cache), so we do a
    5-run warm-up before measuring.
    """
    sample = {
        "pm25": 85.5, "pm10": 120.0, "no2": 45.2, "so2": 18.3,
        "co": 1.2, "o3": 60.0, "nh3": 12.0,
        "temperature": 28.5, "humidity": 65.0,
        "wind_speed": 3.2, "pressure": 1013.0,
    }

    # Warm-up runs (not measured)
    print(f"\n  Warming up (5 runs)…")
    for _ in range(5):
        predict(dict(sample), model, scaler, feature_names)

    # Measured runs
    print(f"  Running {n_runs} inference latency measurements…")
    latencies = []
    for _ in range(n_runs):
        _, lat = predict(dict(sample), model, scaler, feature_names)
        latencies.append(lat)

    latencies = np.array(latencies)

    print(f"\n{'='*50}")
    print(f"  Inference Latency Report ({n_runs} runs)")
    print(f"{'='*50}")
    print(f"  Model        : {type(model).__name__}")
    print(f"  Min          : {latencies.min():.3f} ms")
    print(f"  Max          : {latencies.max():.3f} ms")
    print(f"  Mean         : {latencies.mean():.3f} ms")
    print(f"  Median (p50) : {np.percentile(latencies, 50):.3f} ms")
    print(f"  p95          : {np.percentile(latencies, 95):.3f} ms")
    print(f"  p99          : {np.percentile(latencies, 99):.3f} ms")
    print(f"  Std dev      : {latencies.std():.3f} ms")
    print(f"  Throughput   : {1000 / latencies.mean():.0f} predictions/sec (single-thread)")
    print(f"{'='*50}")

    # Save latency distribution plot
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Histogram
    axes[0].hist(latencies, bins=30, color="#2d6a4f", edgecolor="white", alpha=0.85)
    axes[0].axvline(latencies.mean(),  color="#e74c3c", lw=2, linestyle="--",
                    label=f"Mean = {latencies.mean():.3f} ms")
    axes[0].axvline(np.percentile(latencies, 95), color="#e67e22", lw=2, linestyle=":",
                    label=f"p95 = {np.percentile(latencies, 95):.3f} ms")
    axes[0].set_xlabel("Latency (ms)")
    axes[0].set_ylabel("Count")
    axes[0].set_title("Inference Latency Distribution", fontweight="bold")
    axes[0].legend()

    # Line plot over run index
    axes[1].plot(latencies, color="#1e3a5f", alpha=0.7, linewidth=0.8)
    axes[1].axhline(latencies.mean(), color="#e74c3c", lw=1.5, linestyle="--",
                    label=f"Mean = {latencies.mean():.3f} ms")
    axes[1].set_xlabel("Run Index")
    axes[1].set_ylabel("Latency (ms)")
    axes[1].set_title("Latency Per Run (Stability Check)", fontweight="bold")
    axes[1].legend()

    plt.suptitle(
        f"Inference Latency Benchmark — {type(model).__name__}  "
        f"({n_runs} runs, post warm-up)",
        fontsize=13, fontweight="bold"
    )
    plt.tight_layout()
    plot_path = os.path.join(REPORTS_DIR, "16_inference_latency.png")
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  Latency plot saved → {plot_path}")

    return latencies


def main():
    parser = argparse.ArgumentParser(description="AQI Sample Predictor with Latency Measurement")
    parser.add_argument("--city",         default="Unknown")
    parser.add_argument("--pm25",         type=float, default=85.5)
    parser.add_argument("--pm10",         type=float, default=120.0)
    parser.add_argument("--no2",          type=float, default=45.2)
    parser.add_argument("--so2",          type=float, default=18.3)
    parser.add_argument("--co",           type=float, default=1.2)
    parser.add_argument("--o3",           type=float, default=60.0)
    parser.add_argument("--nh3",          type=float, default=12.0)
    parser.add_argument("--temperature",  type=float, default=28.5)
    parser.add_argument("--humidity",     type=float, default=65.0)
    parser.add_argument("--wind_speed",   type=float, default=3.2)
    parser.add_argument("--pressure",     type=float, default=1013.0)
    parser.add_argument("--latency-runs", type=int,   default=100,
                        help="Number of runs for latency benchmark (default: 100)")
    args = parser.parse_args()

    model, scaler, features = load_model()

    # ── Single prediction ──────────────────────────────────────────────────────
    input_data = {
        "pm25": args.pm25, "pm10": args.pm10, "no2": args.no2,
        "so2": args.so2, "co": args.co, "o3": args.o3, "nh3": args.nh3,
        "temperature": args.temperature, "humidity": args.humidity,
        "wind_speed": args.wind_speed, "pressure": args.pressure,
    }

    aqi, latency_ms = predict(input_data, model, scaler, features)
    category, advisory = get_aqi_info(aqi)

    print("\n" + "="*50)
    print(f"  AQI Prediction — {args.city}")
    print("="*50)
    print(f"  Predicted AQI  : {aqi}")
    print(f"  Category       : {category}")
    print(f"  Model          : {type(model).__name__}")
    print(f"  Inference time : {latency_ms:.3f} ms")
    print(f"\n  Health Advisory:")
    print(f"  {advisory}")
    print("="*50)

    # ── Batch prediction with latency ──────────────────────────────────────────
    print("\n--- Batch Demo (6 cities) ---")
    batch = [
        {"city": "Delhi",     "pm25": 180, "pm10": 280, "no2": 80,  "so2": 30, "co": 2.5, "o3": 40},
        {"city": "Mumbai",    "pm25": 65,  "pm10": 100, "no2": 40,  "so2": 15, "co": 1.2, "o3": 55},
        {"city": "Bangalore", "pm25": 35,  "pm10": 60,  "no2": 25,  "so2": 8,  "co": 0.8, "o3": 45},
        {"city": "Kolkata",   "pm25": 120, "pm10": 200, "no2": 60,  "so2": 25, "co": 2.0, "o3": 35},
        {"city": "Chennai",   "pm25": 45,  "pm10": 80,  "no2": 30,  "so2": 12, "co": 0.9, "o3": 50},
        {"city": "Hyderabad", "pm25": 55,  "pm10": 95,  "no2": 35,  "so2": 14, "co": 1.1, "o3": 48},
    ]
    cities = [b.pop("city") for b in batch]

    aqis, total_ms, per_sample_ms, throughput = predict_batch(
        batch, model, scaler, features
    )

    print(f"\n{'City':<15} {'AQI':>8}  {'Category'}")
    print("-" * 55)
    for city, a in zip(cities, aqis):
        cat, _ = get_aqi_info(a)
        print(f"{city:<15} {a:>8.1f}  {cat}")

    print(f"\n  Batch latency  : {total_ms:.3f} ms total")
    print(f"  Per sample     : {per_sample_ms:.3f} ms")
    print(f"  Throughput     : {throughput:.0f} predictions/sec")

    # ── Latency benchmark ──────────────────────────────────────────────────────
    run_latency_benchmark(model, scaler, features, n_runs=args.latency_runs)


if __name__ == "__main__":
    main()
