# Services package — import each service module so routes can use:
#   from app.services import auth_service
from . import auth_service
from . import dataset_service
from . import prediction_service
from . import analytics_service
from . import report_service

__all__ = [
    "auth_service",
    "dataset_service",
    "prediction_service",
    "analytics_service",
    "report_service",
]
