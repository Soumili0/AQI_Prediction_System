"""
History Routes  —  /api/v1/history/
GET  /           — paginated AQI readings (historical data browser)
GET  /cities     — distinct cities in historical data
"""

from flask import Blueprint, request, jsonify
from app.models.aqi_reading import AQIReading
from app import db
from sqlalchemy import distinct

history_bp = Blueprint("history", __name__)


@history_bp.get("/")
def get_history():
    """
    Browse historical AQI readings.
    ---
    tags: [History]
    parameters:
      - in: query
        name: city
        type: string
      - in: query
        name: page
        type: integer
        default: 1
      - in: query
        name: per_page
        type: integer
        default: 50
      - in: query
        name: date_from
        type: string
        example: "2023-01-01"
      - in: query
        name: date_to
        type: string
        example: "2023-12-31"
    responses:
      200:
        description: Paginated AQI readings
    """
    city      = request.args.get("city")
    page      = int(request.args.get("page", 1))
    per_page  = min(int(request.args.get("per_page", 50)), 200)
    date_from = request.args.get("date_from")
    date_to   = request.args.get("date_to")

    q = AQIReading.query
    if city:
        q = q.filter(AQIReading.city.ilike(f"%{city}%"))
    if date_from:
        q = q.filter(AQIReading.recorded_at >= date_from)
    if date_to:
        q = q.filter(AQIReading.recorded_at <= date_to)

    pagination = q.order_by(AQIReading.recorded_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify({
        "readings": [r.to_dict() for r in pagination.items],
        "total":    pagination.total,
        "page":     page,
        "per_page": per_page,
        "pages":    pagination.pages,
    }), 200


@history_bp.get("/cities")
def get_cities():
    """
    List all distinct cities in the historical dataset.
    ---
    tags: [History]
    responses:
      200:
        description: List of city names
    """
    cities = [r[0] for r in db.session.query(distinct(AQIReading.city))
                                      .order_by(AQIReading.city).all() if r[0]]
    return jsonify({"cities": cities, "count": len(cities)}), 200
