"""
Admin Routes  —  /api/v1/admin/
All routes require admin role.

GET    /users              — list all users
GET    /users/<id>         — get one user
PUT    /users/<id>         — update user (role, status)
DELETE /users/<id>         — deactivate/delete user
GET    /datasets           — list all datasets
DELETE /datasets/<id>      — force-delete any dataset
GET    /predictions        — all predictions (paginated)
GET    /models             — all trained models
PUT    /models/<id>/activate — set active model
GET    /audit-logs         — audit log browser
GET    /stats              — system-wide stats
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db, limiter
from app.models.user import User
from app.models.dataset import Dataset
from app.models.prediction import Prediction
from app.models.ml_model import MLModel
from app.models.audit_log import AuditLog
from app.utils.decorators import admin_required
from app.utils.audit import log_action

admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/users")
@jwt_required()
@admin_required
def list_users():
    """
    List all users (admin only).
    ---
    tags: [Admin]
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
        default: 50
      - in: query
        name: role
        type: string
      - in: query
        name: search
        type: string
    responses:
      200:
        description: Paginated user list
    """
    page     = int(request.args.get("page", 1))
    per_page = min(int(request.args.get("per_page", 50)), 200)
    role     = request.args.get("role")
    search   = request.args.get("search")

    q = User.query
    if role:
        from app.models.role import Role
        r = Role.query.filter_by(name=role).first()
        if r:
            q = q.filter_by(role_id=r.id)
    if search:
        q = q.filter(
            (User.email.ilike(f"%{search}%")) |
            (User.username.ilike(f"%{search}%"))
        )

    pagination = q.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify({
        "users":    [u.to_dict(include_private=True) for u in pagination.items],
        "total":    pagination.total,
        "page":     page,
        "pages":    pagination.pages,
    }), 200


@admin_bp.get("/users/<int:user_id>")
@jwt_required()
@admin_required
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404
    return jsonify({"user": user.to_dict(include_private=True)}), 200


@admin_bp.put("/users/<int:user_id>")
@jwt_required()
@admin_required
def update_user(user_id):
    """
    Update a user's role or status.
    ---
    tags: [Admin]
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
    requestBody:
      content:
        application/json:
          schema:
            type: object
            properties:
              role:      { type: string, enum: [admin, researcher, policy_maker, citizen] }
              is_active: { type: boolean }
    responses:
      200:
        description: User updated
    """
    admin_id = get_jwt_identity()
    user     = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404

    data = request.get_json(silent=True) or {}
    old  = user.to_dict()

    if "role" in data:
        from app.models.role import Role
        role = Role.query.filter_by(name=data["role"]).first()
        if not role:
            return jsonify({"error": f"Unknown role: {data['role']}"}), 400
        user.role_id = role.id

    if "is_active" in data:
        user.is_active = bool(data["is_active"])

    if "is_verified" in data:
        user.is_verified = bool(data["is_verified"])

    db.session.commit()
    log_action("admin.update_user", entity="users", entity_id=user_id,
               old_value=old, new_value=user.to_dict(), user_id=admin_id)
    return jsonify({"user": user.to_dict(), "message": "User updated."}), 200


@admin_bp.delete("/users/<int:user_id>")
@jwt_required()
@admin_required
def delete_user(user_id):
    admin_id = get_jwt_identity()
    if admin_id == user_id:
        return jsonify({"error": "Cannot delete your own account."}), 400
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404
    user.is_active = False
    db.session.commit()
    log_action("admin.deactivate_user", entity="users", entity_id=user_id, user_id=admin_id)
    return jsonify({"message": "User deactivated."}), 200


@admin_bp.get("/datasets")
@jwt_required()
@admin_required
def list_all_datasets():
    page     = int(request.args.get("page", 1))
    per_page = min(int(request.args.get("per_page", 50)), 200)
    pagination = Dataset.query.order_by(Dataset.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify({
        "datasets": [d.to_dict() for d in pagination.items],
        "total":    pagination.total,
        "page":     page,
        "pages":    pagination.pages,
    }), 200


@admin_bp.delete("/datasets/<int:dataset_id>")
@jwt_required()
@admin_required
def admin_delete_dataset(dataset_id):
    dataset = Dataset.query.get(dataset_id)
    if not dataset:
        return jsonify({"error": "Dataset not found."}), 404
    db.session.delete(dataset)
    db.session.commit()
    log_action("admin.delete_dataset", entity="datasets",
               entity_id=dataset_id, user_id=get_jwt_identity())
    return jsonify({"message": "Dataset deleted."}), 200


@admin_bp.get("/predictions")
@jwt_required()
@admin_required
def list_all_predictions():
    page     = int(request.args.get("page", 1))
    per_page = min(int(request.args.get("per_page", 50)), 200)
    pagination = Prediction.query.order_by(
        Prediction.requested_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "predictions": [p.to_dict() for p in pagination.items],
        "total":       pagination.total,
        "page":        page,
        "pages":       pagination.pages,
    }), 200


@admin_bp.get("/models")
@jwt_required()
@admin_required
def list_models():
    models = MLModel.query.order_by(MLModel.trained_at.desc()).all()
    return jsonify({"models": [m.to_dict() for m in models]}), 200


@admin_bp.put("/models/<int:model_id>/activate")
@jwt_required()
@admin_required
def activate_model(model_id):
    """Set a model as the active production model."""
    admin_id = get_jwt_identity()
    model = MLModel.query.get(model_id)
    if not model:
        return jsonify({"error": "Model not found."}), 404

    # Deactivate all others
    MLModel.query.update({"is_active": False})
    model.is_active = True
    db.session.commit()

    # Reset predictor singleton so next request loads the new model
    from app.ml.predictor import reset_predictor
    reset_predictor()

    log_action("admin.activate_model", entity="ml_models",
               entity_id=model_id, user_id=admin_id)
    return jsonify({"message": f"Model '{model.name}' is now active."}), 200


@admin_bp.get("/audit-logs")
@jwt_required()
@admin_required
def get_audit_logs():
    """
    Browse audit logs.
    ---
    tags: [Admin]
    security:
      - BearerAuth: []
    parameters:
      - in: query
        name: action
        type: string
      - in: query
        name: user_id
        type: integer
      - in: query
        name: page
        type: integer
        default: 1
    responses:
      200:
        description: Paginated audit log entries
    """
    page     = int(request.args.get("page", 1))
    per_page = min(int(request.args.get("per_page", 50)), 200)
    action   = request.args.get("action")
    uid      = request.args.get("user_id")

    q = AuditLog.query
    if action:
        q = q.filter(AuditLog.action.ilike(f"%{action}%"))
    if uid:
        q = q.filter_by(user_id=int(uid))

    pagination = q.order_by(AuditLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify({
        "logs":  [log.to_dict() for log in pagination.items],
        "total": pagination.total,
        "page":  page,
        "pages": pagination.pages,
    }), 200


@admin_bp.get("/stats")
@jwt_required()
@admin_required
def system_stats():
    """System-wide statistics."""
    from app.models.aqi_reading import AQIReading
    return jsonify({
        "total_users":       User.query.count(),
        "active_users":      User.query.filter_by(is_active=True).count(),
        "total_datasets":    Dataset.query.count(),
        "total_readings":    AQIReading.query.count(),
        "total_predictions": Prediction.query.count(),
        "total_models":      MLModel.query.count(),
        "active_model":      MLModel.query.filter_by(is_active=True).first().name
                             if MLModel.query.filter_by(is_active=True).first() else None,
    }), 200
