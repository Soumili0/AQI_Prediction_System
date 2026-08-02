"""
Analytics Routes  —  /api/v1/analytics/
GET  /overview           — AQI stats for a city/period
GET  /trend              — time-series trend data
GET  /cities             — city comparison
GET  /pollutants         — pollutant averages
GET  /models             — model comparison metrics
GET  /prediction-stats   — prediction activity summary
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services import analytics_service

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.get("/overview")
def get_overview():
    """
    AQI statistics overview.
    ---
    tags: [Analytics]
    parameters:
      - in: query
        name: city
        type: string
      - in: query
        name: days
        type: integer
        default: 30
    responses:
      200:
        description: AQI stats
    """
    city = request.args.get("city")
    days = int(request.args.get("days", 30))
    return jsonify(analytics_service.get_aqi_overview(city=city, days=days)), 200


@analytics_bp.get("/trend")
def get_trend():
    """
    Time-series AQI trend.
    ---
    tags: [Analytics]
    parameters:
      - in: query
        name: city
        type: string
      - in: query
        name: granularity
        type: string
        enum: [daily, monthly, yearly]
        default: daily
      - in: query
        name: days
        type: integer
        default: 90
    responses:
      200:
        description: Trend data
    """
    city        = request.args.get("city")
    granularity = request.args.get("granularity", "daily")
    days        = int(request.args.get("days", 90))

    if granularity not in ("daily", "monthly", "yearly"):
        return jsonify({"error": "granularity must be daily, monthly, or yearly"}), 400

    return jsonify(analytics_service.get_aqi_trend(city=city, granularity=granularity, days=days)), 200


@analytics_bp.get("/cities")
def get_cities():
    """
    AQI comparison across all cities.
    ---
    tags: [Analytics]
    responses:
      200:
        description: City-level AQI stats
    """
    return jsonify(analytics_service.get_city_comparison()), 200


@analytics_bp.get("/pollutants")
def get_pollutants():
    """
    Average pollutant concentrations.
    ---
    tags: [Analytics]
    parameters:
      - in: query
        name: city
        type: string
      - in: query
        name: days
        type: integer
        default: 30
    responses:
      200:
        description: Pollutant averages
    """
    city = request.args.get("city")
    days = int(request.args.get("days", 30))
    return jsonify(analytics_service.get_pollutant_averages(city=city, days=days)), 200


@analytics_bp.get("/models")
@jwt_required()
def get_models():
    """
    Trained model comparison metrics.
    ---
    tags: [Analytics]
    security:
      - BearerAuth: []
    responses:
      200:
        description: Model metrics list
    """
    return jsonify({"models": analytics_service.get_model_comparison()}), 200


@analytics_bp.get("/prediction-stats")
@jwt_required()
def get_pred_stats():
    """
    Prediction activity summary for the current user.
    ---
    tags: [Analytics]
    security:
      - BearerAuth: []
    parameters:
      - in: query
        name: days
        type: integer
        default: 30
    responses:
      200:
        description: Prediction stats
    """
    user_id = int(get_jwt_identity())
    days    = int(request.args.get("days", 30))
    return jsonify(analytics_service.get_prediction_stats(user_id=user_id, days=days)), 200
