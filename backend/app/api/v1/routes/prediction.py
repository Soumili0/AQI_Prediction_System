"""
Prediction Routes
=================
POST /           — predict AQI (authenticated or anonymous)
POST /batch      — predict for multiple inputs
GET  /<id>       — get one prediction with full explanation
GET  /history    — paginated history for current user
POST /explain    — SHAP + LIME explanation for given input
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from app import limiter
from app.services import prediction_service

prediction_bp = Blueprint("prediction", __name__)


@prediction_bp.post("/")
@limiter.limit("60 per hour")
def predict():
    """
    Predict AQI from pollutant and weather features.
    ---
    tags:
      - Predictions
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [pm25, pm10, no2, so2, co, o3]
            properties:
              pm25:         { type: number, example: 85.5 }
              pm10:         { type: number, example: 120.0 }
              no2:          { type: number, example: 45.2 }
              so2:          { type: number, example: 18.3 }
              co:           { type: number, example: 1.2 }
              o3:           { type: number, example: 60.0 }
              nh3:          { type: number, example: 12.0 }
              temperature:  { type: number, example: 28.5 }
              humidity:     { type: number, example: 65.0 }
              wind_speed:   { type: number, example: 3.2 }
              wind_direction: { type: number, example: 180 }
              pressure:     { type: number, example: 1013.0 }
              city:         { type: string, example: "Delhi" }
    responses:
      200:
        description: Prediction result with AQI, category, advisory, and SHAP explanation
      400:
        description: Missing required features
      503:
        description: Model not loaded — run training first
    """
    # Optional authentication
    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        uid = get_jwt_identity()
        user_id = int(uid) if uid else None
    except Exception:
        pass

    data = request.get_json(silent=True) or {}
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    try:
        result = prediction_service.predict_aqi(data, user_id=user_id)
        return jsonify(result), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc), "hint": "Model not trained yet."}), 503
    except Exception as exc:
        from flask import current_app
        current_app.logger.error("Prediction error: %s", exc, exc_info=True)
        return jsonify({"error": "Prediction failed. Please try again."}), 500


@prediction_bp.post("/batch")
@jwt_required()
@limiter.limit("10 per hour")
def predict_batch():
    """
    Predict AQI for multiple records at once.
    ---
    tags:
      - Predictions
    security:
      - BearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [records]
            properties:
              records:
                type: array
                items:
                  type: object
                maxItems: 500
    responses:
      200:
        description: List of predicted AQI values
      400:
        description: Invalid input
    """
    data = request.get_json(silent=True) or {}
    records = data.get("records", [])
    if not records or not isinstance(records, list):
        return jsonify({"error": "'records' must be a non-empty list."}), 400
    if len(records) > 500:
        return jsonify({"error": "Maximum 500 records per batch request."}), 400

    try:
        from app.ml.predictor import get_predictor
        predictor = get_predictor()
        predictions = predictor.predict_batch(records)
        from app.models.prediction import get_aqi_category
        results = []
        for pred, rec in zip(predictions, records):
            cat, adv = get_aqi_category(pred)
            results.append({
                "predicted_aqi": pred,
                "aqi_category": cat,
                "health_advisory": adv,
                "city": rec.get("city"),
            })
        return jsonify({"predictions": results, "count": len(results)}), 200
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@prediction_bp.get("/history")
@jwt_required()
def prediction_history():
    """
    Get prediction history for the current user.
    ---
    tags:
      - Predictions
    security:
      - BearerAuth: []
    parameters:
      - in: query
        name: page
        type: integer
        default: 1
      - in: query
        name: per_page
        type: integer
        default: 20
    responses:
      200:
        description: Paginated prediction history
    """
    user_id  = int(get_jwt_identity())
    page     = int(request.args.get("page", 1))
    per_page = min(int(request.args.get("per_page", 20)), 100)
    result   = prediction_service.get_prediction_history(user_id, page, per_page)
    return jsonify(result), 200


@prediction_bp.get("/<int:pred_id>")
@jwt_required()
def get_prediction(pred_id):
    """
    Get a single prediction record with full explanation.
    ---
    tags:
      - Predictions
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: pred_id
        type: integer
        required: true
    responses:
      200:
        description: Prediction detail
      404:
        description: Not found
    """
    user_id = int(get_jwt_identity())
    from app.models.prediction import Prediction
    from app.models.user import User
    pred = Prediction.query.get(pred_id)
    if not pred:
        return jsonify({"error": "Prediction not found."}), 404

    user = User.query.get(user_id)
    if pred.user_id != user_id and not (user and user.is_admin()):
        return jsonify({"error": "Access denied."}), 403

    return jsonify({"prediction": pred.to_dict()}), 200


@prediction_bp.post("/explain")
@jwt_required()
@limiter.limit("30 per hour")
def explain():
    """
    Generate SHAP + LIME explanations for a given input.
    ---
    tags:
      - Predictions
    security:
      - BearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [features]
            properties:
              features:
                type: object
                description: Feature dict (same as /predictions/)
              methods:
                type: array
                items: { type: string, enum: [shap, lime] }
                default: [shap, lime]
    responses:
      200:
        description: Explanation results from SHAP and/or LIME
      503:
        description: Model not loaded
    """
    data    = request.get_json(silent=True) or {}
    features = data.get("features", {})
    methods  = data.get("methods", ["shap", "lime"])

    if not features:
        return jsonify({"error": "'features' is required."}), 400

    try:
        import numpy as np
        from app.ml.predictor import get_predictor
        from app.xai.explainer import explain_shap, explain_lime
        from app.services.prediction_service import _enrich_with_time_features

        predictor = get_predictor()
        enriched  = _enrich_with_time_features(dict(features))
        pred_res  = predictor.predict(enriched)
        X_scaled  = np.array(pred_res["feature_vector_scaled"]).reshape(1, -1)

        response = {
            "predicted_aqi": pred_res["predicted_aqi"],
            "feature_names": predictor.feature_names,
        }

        if "shap" in methods:
            response["shap"] = explain_shap(predictor.model, X_scaled, predictor.feature_names)

        if "lime" in methods:
            # Use a small identity matrix as background when no training data available
            bg = np.zeros((50, X_scaled.shape[1]))
            response["lime"] = explain_lime(predictor.model, X_scaled.flatten(),
                                            predictor.feature_names, bg)

        return jsonify(response), 200

    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:
        from flask import current_app
        current_app.logger.error("Explanation error: %s", exc, exc_info=True)
        return jsonify({"error": f"Explanation failed: {exc}"}), 500
