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


def require_roles(*roles: str):
    """Decorator: allow only users whose role matches one of `roles`.

    Must be applied AFTER @jwt_required() so that the JWT identity is
    already available.

    Args:
        *roles: One or more role name strings.

    Returns:
        Decorated function that returns 403 if the role check fails.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)

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
    """Decorator: ensure the JWT user is active and verified.

    Must be applied AFTER @jwt_required().
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404

        if not user.is_active:
            return jsonify({"error": "Account is deactivated. Contact support."}), 403

        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    """Shortcut decorator for admin-only endpoints."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        from flask_jwt_extended import get_jwt_identity
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user or not user.is_admin():
            return jsonify({"error": "Admin access required"}), 403

        return fn(*args, **kwargs)
    return wrapper
