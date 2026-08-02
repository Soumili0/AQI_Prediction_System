"""
Application Factory
===================
Uses the factory pattern to allow multiple configurations (dev, test, prod)
and makes testing easier by avoiding a global app instance.
"""

# PyMySQL as MySQLdb drop-in replacement (required for Python 3.13+)
import pymysql
pymysql.install_as_MySQLdb()

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flasgger import Swagger

from .core.config import config_by_name
from .core.logging import setup_logging

# ---------------------------------------------------------------------------
# Extension singletons (not yet bound to any app)
# ---------------------------------------------------------------------------
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
bcrypt = Bcrypt()
mail = Mail()
limiter = Limiter(key_func=get_remote_address)


def create_app(config_name: str = "development") -> Flask:
    """Create and configure the Flask application.

    Args:
        config_name: One of 'development', 'testing', 'production'.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__, instance_relative_config=True)

    # ------------------------------------------------------------------
    # Load configuration
    # ------------------------------------------------------------------
    app.config.from_object(config_by_name[config_name])

    # ------------------------------------------------------------------
    # Initialise extensions
    # ------------------------------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)

    CORS(
        app,
        resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}},
        supports_credentials=True,
    )

    # Swagger / OpenAPI documentation
    Swagger(app, config=app.config.get("SWAGGER_CONFIG", {}), merge=True)

    # ------------------------------------------------------------------
    # Setup structured logging
    # ------------------------------------------------------------------
    setup_logging(app)

    # ------------------------------------------------------------------
    # Register Blueprints
    # ------------------------------------------------------------------
    from .api.v1 import api_v1_bp
    app.register_blueprint(api_v1_bp, url_prefix="/api/v1")

    # ------------------------------------------------------------------
    # JWT error handlers
    # ------------------------------------------------------------------
    _register_jwt_handlers(jwt)

    # ------------------------------------------------------------------
    # Global error handlers
    # ------------------------------------------------------------------
    _register_error_handlers(app)

    # ------------------------------------------------------------------
    # Security headers (applied to every response)
    # ------------------------------------------------------------------
    from .core.security import apply_security_headers
    app.after_request(apply_security_headers)

    # ------------------------------------------------------------------
    # Register CLI commands
    # ------------------------------------------------------------------
    from .core.cli import register_commands
    register_commands(app)

    # ------------------------------------------------------------------
    # Shell context (for `flask shell`)
    # ------------------------------------------------------------------
    @app.shell_context_processor
    def make_shell_context():  # noqa: WPS430
        from .models.user import User
        from .models.prediction import Prediction
        from .models.dataset import Dataset
        from .models.audit_log import AuditLog
        return {"db": db, "User": User, "Prediction": Prediction,
                "Dataset": Dataset, "AuditLog": AuditLog}

    return app


def _register_jwt_handlers(jwt_manager: JWTManager) -> None:
    """Attach custom JWT error callbacks."""
    from flask import jsonify

    @jwt_manager.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"error": "Token has expired", "code": "TOKEN_EXPIRED"}), 401

    @jwt_manager.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"error": "Invalid token", "code": "INVALID_TOKEN"}), 401

    @jwt_manager.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"error": "Authentication token is required", "code": "MISSING_TOKEN"}), 401

    @jwt_manager.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({"error": "Token has been revoked", "code": "TOKEN_REVOKED"}), 401


def _register_error_handlers(app: Flask) -> None:
    """Global HTTP error handlers."""
    from flask import jsonify

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad request", "message": str(e)}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"error": "Unauthorized", "message": str(e)}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"error": "Forbidden", "message": str(e)}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found", "message": str(e)}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed", "message": str(e)}), 405

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return jsonify({"error": "Rate limit exceeded", "message": str(e)}), 429

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error(f"Internal server error: {e}")
        return jsonify({"error": "Internal server error"}), 500
