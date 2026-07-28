"""
Prediction Service
==================
Orchestrates the full prediction lifecycle:
  1. Validate input
  2. Derive time features
  3. Run ML predictor
  4. Determine AQI category + health advisory
  5. Generate SHAP explanation
  6. Persist result to DB
  7. Return rich response dict
"""

from datetime import datetime
from flask import request

from app import db
from app.ml.predictor import get_predictor
from app.models.prediction import Prediction, get_aqi_category
from app.models.ml_model import MLModel
from app.utils.audit import log_action

REQUIRED_FEATURES = ["pm25", "pm10", "no2", "so2", "co", "o3"]


def _enrich_with_time_features(data: dict) -> dict:
    """Add hour, day_of_week, month, year, is_weekend, season if absent."""
    now = datetime.utcnow()
    defaults = {
        "hour":        now.hour,
        "day_of_week": now.weekday(),
        "month":       now.month,
        "year":        now.year,
        "is_weekend":  int(now.weekday() in (5, 6)),
        "season":      {12:0,1:0,2:0,3:1,4:1,5:1,6:2,7:2,8:2,9:3,10:3,11:3}[now.month],
    }
    for k, v in defaults.items():
        data.setdefault(k, v)
    return data


def predict_aqi(input_data: dict, user_id: int = None) -> dict:
    """Full prediction pipeline for a single request.

    Args:
        input_data: Dict of pollutant/weather feature values.
        user_id:    Authenticated user ID (or None for anonymous).

    Returns:
        Rich dict with predicted_aqi, category, advisory, explanation, etc.

    Raises:
        ValueError: on missing required features.
    """
    # Validate required pollutants
    missing = [f for f in REQUIRED_FEATURES if f not in input_data or input_data[f] is None]
    if missing:
        raise ValueError(f"Missing required features: {missing}")

    # Enrich with time features
    features = _enrich_with_time_features(dict(input_data))

    # Get predictor singleton
    predictor = get_predictor()

    # Run prediction
    pred_result = predictor.predict(features)
    predicted_aqi = pred_result["predicted_aqi"]

    # Category + health advisory
    category, advisory = get_aqi_category(predicted_aqi)

    # SHAP explanation (graceful fallback if it fails)
    explanation = None
    try:
        import numpy as np
        from app.xai.explainer import explain_shap
        X_sample = np.array(pred_result["feature_vector_scaled"]).reshape(1, -1)
        shap_result = explain_shap(
            model=predictor.model,
            X_sample=X_sample,
            feature_names=predictor.feature_names,
        )
        # Keep only the JSON-serialisable parts for the DB
        explanation = {
            "method": shap_result["method"],
            "base_value": shap_result["base_value"],
            "feature_importance": shap_result["feature_importance"],
        }
        # Attach plot for the response (not stored in DB)
        explanation["waterfall_plot_b64"] = shap_result.get("waterfall_plot_b64")
    except Exception as exc:
        from flask import current_app
        current_app.logger.warning("SHAP explanation failed: %s", exc)

    # Persist to DB
    ip = _get_client_ip()
    active_model = MLModel.query.filter_by(is_active=True).first()

    record = Prediction(
        user_id=user_id,
        model_id=active_model.id if active_model else None,
        city=str(input_data.get("city", ""))[:100] or None,
        input_features=features,
        predicted_aqi=predicted_aqi,
        aqi_category=category,
        health_advisory=advisory,
        explanation={k: v for k, v in (explanation or {}).items()
                     if k != "waterfall_plot_b64"},
        ip_address=ip,
    )
    db.session.add(record)
    db.session.commit()

    if user_id:
        log_action("prediction.create", entity="predictions",
                   entity_id=record.id, user_id=user_id)

    return {
        "id": record.id,
        "predicted_aqi": predicted_aqi,
        "aqi_category": category,
        "health_advisory": advisory,
        "input_features": features,
        "explanation": explanation,
        "requested_at": record.requested_at.isoformat(),
        "model": active_model.name if active_model else "unknown",
    }


def get_prediction_history(user_id: int, page: int = 1, per_page: int = 20) -> dict:
    """Paginated prediction history for a user."""
    pagination = (
        Prediction.query
        .filter_by(user_id=user_id)
        .order_by(Prediction.requested_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    return {
        "predictions": [p.to_dict() for p in pagination.items],
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
        "pages": pagination.pages,
    }


def _get_client_ip() -> str:
    try:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.remote_addr or "unknown"
    except RuntimeError:
        return "unknown"
