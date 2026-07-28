"""
API v1 Blueprint Registration
==============================
All route blueprints are imported and registered here under the /api/v1 prefix.
"""

from flask import Blueprint

api_v1_bp = Blueprint("api_v1", __name__)

# Import and register child blueprints
from .routes.auth import auth_bp
from .routes.prediction import prediction_bp
from .routes.dataset import dataset_bp
from .routes.analytics import analytics_bp
from .routes.reports import reports_bp
from .routes.admin import admin_bp
from .routes.history import history_bp

api_v1_bp.register_blueprint(auth_bp, url_prefix="/auth")
api_v1_bp.register_blueprint(prediction_bp, url_prefix="/predictions")
api_v1_bp.register_blueprint(dataset_bp, url_prefix="/datasets")
api_v1_bp.register_blueprint(analytics_bp, url_prefix="/analytics")
api_v1_bp.register_blueprint(reports_bp, url_prefix="/reports")
api_v1_bp.register_blueprint(admin_bp, url_prefix="/admin")
api_v1_bp.register_blueprint(history_bp, url_prefix="/history")
