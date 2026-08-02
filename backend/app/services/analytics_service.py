"""
Analytics Service
=================
Produces aggregated analytics data for dashboard charts:
  - AQI statistics overview
  - Trend data (daily / monthly / yearly)
  - City comparison
  - Pollutant averages
  - AQI category breakdown
  - Model comparison metrics
"""

from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import func, case
from app import db
from app.models.aqi_reading import AQIReading
from app.models.prediction import Prediction
from app.models.ml_model import MLModel


def _get_advisory(aqi: float) -> str:
    if aqi is None:
        return "Monitor air quality regularly."
    if aqi <= 50:   return "Air quality is good. Enjoy outdoor activities."
    if aqi <= 100:  return "Air quality is acceptable. Sensitive individuals should limit prolonged outdoor exertion."
    if aqi <= 200:  return "Members of sensitive groups may experience health effects. General public is less likely to be affected."
    if aqi <= 300:  return "Everyone may begin to experience health effects. Sensitive groups should avoid outdoor exertion."
    if aqi <= 400:  return "Health alert: everyone may experience serious health effects. Avoid outdoor activities."
    return "Emergency conditions. Everyone should avoid all outdoor activities."


def get_aqi_overview(city: str = None, days: int = 30) -> dict:
    """Current AQI stats: mean, min, max, category breakdown."""
    since = datetime.utcnow() - timedelta(days=days)
    q = AQIReading.query.filter(AQIReading.recorded_at >= since)
    if city:
        q = q.filter(AQIReading.city.ilike(f"%{city}%"))

    readings = q.all()
    if not readings:
        return {"message": "No data available for the specified parameters."}

    aqi_values = [r.aqi for r in readings if r.aqi is not None]
    if not aqi_values:
        return {"message": "No AQI values found."}

    # Latest reading for current AQI
    latest = max((r for r in readings if r.aqi is not None),
                 key=lambda r: r.recorded_at, default=None)

    category_counts = {}
    for r in readings:
        if r.aqi_category:
            category_counts[r.aqi_category] = category_counts.get(r.aqi_category, 0) + 1

    return {
        "period_days": days,
        "city": city or "All",
        "total_readings": len(aqi_values),
        "current_aqi": round(float(latest.aqi), 2) if latest else None,
        "aqi_category": latest.aqi_category if latest else None,
        "health_advisory": _get_advisory(latest.aqi) if latest else None,
        "mean_aqi":   round(sum(aqi_values) / len(aqi_values), 2),
        "min_aqi":    round(min(aqi_values), 2),
        "max_aqi":    round(max(aqi_values), 2),
        "category_breakdown": category_counts,
    }


def get_aqi_trend(city: str = None, granularity: str = "daily",
                  days: int = 90) -> dict:
    """Time-series AQI trend at daily, monthly, or yearly granularity."""
    since = datetime.utcnow() - timedelta(days=days)
    q = (db.session.query(
            AQIReading.recorded_at,
            AQIReading.aqi,
            AQIReading.city,
         )
         .filter(AQIReading.recorded_at >= since)
         .filter(AQIReading.aqi.isnot(None)))

    if city:
        q = q.filter(AQIReading.city.ilike(f"%{city}%"))

    rows = q.all()
    if not rows:
        return {"trend": [], "granularity": granularity}

    df = pd.DataFrame(rows, columns=["recorded_at", "aqi", "city"])
    df["recorded_at"] = pd.to_datetime(df["recorded_at"])

    if granularity == "monthly":
        df["period"] = df["recorded_at"].dt.to_period("M").astype(str)
    elif granularity == "yearly":
        df["period"] = df["recorded_at"].dt.year.astype(str)
    else:
        df["period"] = df["recorded_at"].dt.date.astype(str)

    trend = (df.groupby("period")["aqi"]
               .agg(mean="mean", min="min", max="max", count="count")
               .reset_index()
               .rename(columns={"period": "date"}))

    trend["mean"] = trend["mean"].round(2)
    trend["min"]  = trend["min"].round(2)
    trend["max"]  = trend["max"].round(2)

    return {
        "trend": trend.to_dict(orient="records"),
        "granularity": granularity,
        "city": city or "All",
        "period_days": days,
    }


def get_city_comparison() -> dict:
    """Mean AQI and latest reading per city."""
    results = (
        db.session.query(
            AQIReading.city,
            func.avg(AQIReading.aqi).label("mean_aqi"),
            func.min(AQIReading.aqi).label("min_aqi"),
            func.max(AQIReading.aqi).label("max_aqi"),
            func.count(AQIReading.id).label("count"),
        )
        .filter(AQIReading.aqi.isnot(None))
        .group_by(AQIReading.city)
        .order_by(func.avg(AQIReading.aqi).desc())
        .all()
    )

    cities = [
        {
            "city": r.city,
            "mean_aqi": round(float(r.mean_aqi), 2),
            "min_aqi":  round(float(r.min_aqi), 2),
            "max_aqi":  round(float(r.max_aqi), 2),
            "count":    r.count,
        }
        for r in results
    ]
    return {"cities": cities, "total_cities": len(cities)}


def get_pollutant_averages(city: str = None, days: int = 30) -> dict:
    """Mean concentration for each pollutant over the last N days."""
    since = datetime.utcnow() - timedelta(days=days)
    q = AQIReading.query.filter(AQIReading.recorded_at >= since)
    if city:
        q = q.filter(AQIReading.city.ilike(f"%{city}%"))

    rows = q.all()
    if not rows:
        return {"pollutants": {}}

    pollutants = ["pm25", "pm10", "no2", "so2", "co", "o3", "nh3"]
    result = {}
    for p in pollutants:
        vals = [getattr(r, p) for r in rows if getattr(r, p) is not None]
        result[p] = round(sum(vals) / len(vals), 3) if vals else None

    return {"pollutants": result, "period_days": days, "city": city or "All"}


def get_model_comparison() -> list:
    """Return metrics for all trained models from DB."""
    models = MLModel.query.order_by(MLModel.rmse.asc()).all()
    return [m.to_dict() for m in models]


def get_prediction_stats(user_id: int = None, days: int = 30) -> dict:
    """Summary of prediction activity."""
    since = datetime.utcnow() - timedelta(days=days)
    q = Prediction.query.filter(Prediction.requested_at >= since)
    if user_id:
        q = q.filter_by(user_id=user_id)

    total = q.count()
    cats  = {}
    for p in q.all():
        if p.aqi_category:
            cats[p.aqi_category] = cats.get(p.aqi_category, 0) + 1

    return {
        "total_predictions": total,
        "period_days": days,
        "category_breakdown": cats,
    }
