# Import all models so Flask-Migrate can discover them
from .role import Role
from .user import User
from .refresh_token import RefreshToken
from .dataset import Dataset
from .aqi_reading import AQIReading
from .ml_model import MLModel
from .prediction import Prediction
from .report import Report
from .audit_log import AuditLog

__all__ = [
    "Role",
    "User",
    "RefreshToken",
    "Dataset",
    "AQIReading",
    "MLModel",
    "Prediction",
    "Report",
    "AuditLog",
]
