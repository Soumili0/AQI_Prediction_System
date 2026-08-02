"""
RBAC Decorators
===============
Role-Based Access Control decorators that wrap Flask-JWT-Extended's
`@jwt_required()`. Usage:

    @jwt_required()
    @require_roles("admin", "researcher")
    def my_protected_endpoint():
        ...
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from app.models.user import User


def _get_user_id() -> int:
    """Return JWT identity as int (Flask-JWT-Extended 4.x returns str)."""
    return int(get_jwt_identity())


def require_roles(*roles: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = User.query.get(_get_user_id())
            if not user:
                return jsonify({"error": "User not found"}), 404
            if not user.is_active:
                return jsonify({"error": "Account is deactivated"}), 403
            if user.role_name not in roles:
                return jsonify({
                    "error": "Forbidden",
                    "message": f"Requires one of roles: {list(roles)}. Your role: {user.role_name}"
                }), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_active_user(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = User.query.get(_get_user_id())
        if not user:
            return jsonify({"error": "User not found"}), 404
        if not user.is_active:
            return jsonify({"error": "Account is deactivated. Contact support."}), 403
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = User.query.get(_get_user_id())
        if not user or not user.is_admin():
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper
