"""
Dataset Routes
==============
Endpoints under /api/v1/datasets/

POST   /upload          — upload CSV/XLSX
POST   /fetch-openaq    — fetch from OpenAQ API
GET    /                — list datasets
GET    /<id>            — get single dataset
DELETE /<id>            — delete dataset
GET    /<id>/readings   — paginated readings from a dataset
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import limiter
from app.services import dataset_service
from app.utils.decorators import require_roles

dataset_bp = Blueprint("dataset", __name__)


@dataset_bp.post("/upload")
@jwt_required()
@limiter.limit("20 per hour")
def upload_dataset():
    """
    Upload a CSV or XLSX dataset file.
    ---
    tags:
      - Datasets
    security:
      - BearerAuth: []
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: file
        type: file
        required: true
      - in: formData
        name: name
        type: string
        required: true
      - in: formData
        name: description
        type: string
      - in: formData
        name: location
        type: string
      - in: formData
        name: is_public
        type: boolean
    responses:
      201:
        description: Dataset uploaded and processed
      400:
        description: Validation error
    """
    user_id = get_jwt_identity()

    if "file" not in request.files:
        return jsonify({"error": "No file provided."}), 400

    file = request.files["file"]
    name = request.form.get("name", "").strip()
    if not name:
        return jsonify({"error": "Dataset name is required."}), 400

    description = request.form.get("description", "")
    location = request.form.get("location", "")
    is_public = request.form.get("is_public", "false").lower() == "true"

    try:
        result = dataset_service.upload_csv_dataset(
            file=file, user_id=user_id, name=name,
            description=description, location=location, is_public=is_public,
        )
        return jsonify({"dataset": result, "message": "Dataset uploaded and processed."}), 201
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@dataset_bp.post("/fetch-openaq")
@jwt_required()
@require_roles("admin", "researcher")
@limiter.limit("10 per hour")
def fetch_openaq():
    """
    Fetch air quality data from OpenAQ API.
    ---
    tags:
      - Datasets
    security:
      - BearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [city, country, date_from, date_to]
            properties:
              city:       { type: string, example: "Delhi" }
              country:    { type: string, example: "IN" }
              date_from:  { type: string, example: "2024-01-01" }
              date_to:    { type: string, example: "2024-01-31" }
              limit:      { type: integer, default: 10000 }
    responses:
      201:
        description: Data fetched and stored
      400:
        description: API error or no data
    """
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    required = ["city", "country", "date_from", "date_to"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    try:
        result = dataset_service.fetch_openaq_data(
            city=data["city"],
            country=data["country"],
            date_from=data["date_from"],
            date_to=data["date_to"],
            user_id=user_id,
            limit=data.get("limit", 10000),
        )
        return jsonify({"dataset": result, "message": "OpenAQ data fetched."}), 201
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@dataset_bp.get("/")
@jwt_required()
def list_datasets():
    """
    List all datasets accessible to the current user.
    ---
    tags:
      - Datasets
    security:
      - BearerAuth: []
    responses:
      200:
        description: List of datasets
    """
    user_id = get_jwt_identity()
    include_public = request.args.get("include_public", "true").lower() == "true"
    datasets = dataset_service.get_dataset_list(user_id, include_public)
    return jsonify({"datasets": datasets, "count": len(datasets)}), 200


@dataset_bp.get("/<int:dataset_id>")
@jwt_required()
def get_dataset(dataset_id):
    """
    Get metadata for a specific dataset.
    ---
    tags:
      - Datasets
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: dataset_id
        type: integer
        required: true
    responses:
      200:
        description: Dataset metadata
      404:
        description: Not found
    """
    from app.models.dataset import Dataset
    dataset = Dataset.query.get(dataset_id)
    if not dataset:
        return jsonify({"error": "Dataset not found."}), 404
    return jsonify({"dataset": dataset.to_dict()}), 200


@dataset_bp.delete("/<int:dataset_id>")
@jwt_required()
def delete_dataset(dataset_id):
    """
    Delete a dataset (owner or admin only).
    ---
    tags:
      - Datasets
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: dataset_id
        type: integer
        required: true
    responses:
      200:
        description: Dataset deleted
      403:
        description: Permission denied
      404:
        description: Not found
    """
    user_id = get_jwt_identity()
    try:
        dataset_service.delete_dataset(dataset_id, user_id)
        return jsonify({"message": "Dataset deleted successfully."}), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    except PermissionError as exc:
        return jsonify({"error": str(exc)}), 403


@dataset_bp.get("/<int:dataset_id>/readings")
@jwt_required()
def get_readings(dataset_id):
    """
    Get paginated readings from a dataset.
    ---
    tags:
      - Datasets
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: dataset_id
        type: integer
        required: true
      - in: query
        name: page
        type: integer
        default: 1
      - in: query
        name: per_page
        type: integer
        default: 100
    responses:
      200:
        description: Paginated readings
    """
    from app.models.aqi_reading import AQIReading
    page = int(request.args.get("page", 1))
    per_page = min(int(request.args.get("per_page", 100)), 500)

    pagination = (
        AQIReading.query
        .filter_by(dataset_id=dataset_id)
        .order_by(AQIReading.recorded_at.asc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return jsonify({
        "readings": [r.to_dict() for r in pagination.items],
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
        "pages": pagination.pages,
    }), 200
