"""
Sample Prediction Script
=========================
Demonstrates how to load the trained model and make predictions
without the Flask API. Useful for testing and batch offline jobs.

Usage:
  python ml/scripts/predict_sample.py
  python ml/scripts/predict_sample.py --city Delhi --pm25 120 --pm10 200
"""

import os, sys, json, argparse
import numpy as np
import joblib
from datetime import datetime

ROOT        = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODELS_DIR  = os.path.join(ROOT, "models")

AQI_CATEGORIES = [
    (0,   50,  "Good",                          "Air quality is satisfactory."),
    (51,  100, "Moderate",                      "Acceptable quality; sensitive individuals should take precautions."),
    (101, 150, "Unhealthy for Sensitive Groups", "Sensitive groups may experience health effects."),
    (151, 200, "Unhealthy",                     "Everyone may begin to experience health effects."),
    (201, 300, "Very Unhealthy",                "Health alert: risk is increased for everyone."),
    (301, 500, "Hazardous",                     "Emergency conditions — serious risk."),
]

FEATURE_COLS = [
    "pm25","pm10","no2","so2","co","o3","nh3",
    "temperature","humidity","wind_speed","wind_direction","pressure",
    "hour","day_of_week","month","year","is_weekend","season",
]


def load_model():
    model_path   = os.path.join(MODELS_DIR, "aqi_model.pkl")
    scaler_path  = os.path.join(MODELS_DIR, "scaler.pkl")
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
    now = datetime.utcnow()
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
    scaled = scaler.transform(vector)
    aqi    = max(0.0, round(float(model.predict(scaled)[0]), 2))
    return aqi


def main():
    parser = argparse.ArgumentParser(description="AQI Sample Predictor")
    parser.add_argument("--city",      default="Unknown")
    parser.add_argument("--pm25",      type=float, default=85.5)
    parser.add_argument("--pm10",      type=float, default=120.0)
    parser.add_argument("--no2",       type=float, default=45.2)
    parser.add_argument("--so2",       type=float, default=18.3)
    parser.add_argument("--co",        type=float, default=1.2)
    parser.add_argument("--o3",        type=float, default=60.0)
    parser.add_argument("--nh3",       type=float, default=12.0)
    parser.add_argument("--temperature",type=float,default=28.5)
    parser.add_argument("--humidity",  type=float, default=65.0)
    parser.add_argument("--wind_speed",type=float, default=3.2)
    parser.add_argument("--pressure",  type=float, default=1013.0)
    args = parser.parse_args()

    model, scaler, features = load_model()

    input_data = {
        "pm25": args.pm25, "pm10": args.pm10, "no2": args.no2,
        "so2": args.so2, "co": args.co, "o3": args.o3, "nh3": args.nh3,
        "temperature": args.temperature, "humidity": args.humidity,
        "wind_speed": args.wind_speed, "pressure": args.pressure,
    }

    aqi = predict(input_data, model, scaler, features)
    category, advisory = get_aqi_info(aqi)

    print("\n" + "="*50)
    print(f"  AQI Prediction — {args.city}")
    print("="*50)
    print(f"  Predicted AQI : {aqi}")
    print(f"  Category      : {category}")
    print(f"  Model         : {type(model).__name__}")
    print(f"\n  Health Advisory:")
    print(f"  {advisory}")
    print("="*50)

    # Run a batch of sample cities
    print("\n--- Batch Demo (6 cities) ---")
    batch = [
        {"city": "Delhi",     "pm25": 180, "pm10": 280, "no2": 80,  "so2": 30, "co": 2.5, "o3": 40},
        {"city": "Mumbai",    "pm25": 65,  "pm10": 100, "no2": 40,  "so2": 15, "co": 1.2, "o3": 55},
        {"city": "Bangalore", "pm25": 35,  "pm10": 60,  "no2": 25,  "so2": 8,  "co": 0.8, "o3": 45},
        {"city": "Kolkata",   "pm25": 120, "pm10": 200, "no2": 60,  "so2": 25, "co": 2.0, "o3": 35},
        {"city": "Chennai",   "pm25": 45,  "pm10": 80,  "no2": 30,  "so2": 12, "co": 0.9, "o3": 50},
        {"city": "Hyderabad", "pm25": 55,  "pm10": 95,  "no2": 35,  "so2": 14, "co": 1.1, "o3": 48},
    ]

    print(f"\n{'City':<15} {'AQI':>8} {'Category'}")
    print("-" * 55)
    for b in batch:
        city = b.pop("city")
        a = predict(b, model, scaler, features)
        cat, _ = get_aqi_info(a)
        print(f"{city:<15} {a:>8.1f}  {cat}")


if __name__ == "__main__":
    main()
