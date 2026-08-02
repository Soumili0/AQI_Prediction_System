"""
Application Configuration
==========================
Three-tier config hierarchy: base → development / testing / production.
Loaded from environment variables via python-dotenv.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    """Shared settings for all environments."""

    # Flask
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    JSON_SORT_KEYS: bool = False

    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ECHO: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: dict = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 10,
        "max_overflow": 20,
    }

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "jwt-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(
        seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 3600))
    )
    JWT_REFRESH_TOKEN_EXPIRES: timedelta = timedelta(
        seconds=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", 2592000))
    )
    JWT_TOKEN_LOCATION: list = ["headers"]
    JWT_HEADER_NAME: str = "Authorization"
    JWT_HEADER_TYPE: str = "Bearer"
    JWT_DECODE_LEEWAY: int = 10

    # Email
    MAIL_SERVER: str = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS: bool = os.getenv("MAIL_USE_TLS", "True") == "True"
    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER: str = os.getenv("MAIL_DEFAULT_SENDER", "noreply@aqiprediction.com")

    # CORS
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

    # Rate limiting
    RATELIMIT_DEFAULT: str = os.getenv("RATELIMIT_DEFAULT", "200 per day;50 per hour")
    RATELIMIT_STORAGE_URL: str = os.getenv("RATELIMIT_STORAGE_URL", "memory://")

    # ML — resolve paths relative to project root (one level above backend/)
    _BASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    MODEL_PATH: str = os.getenv(
        "MODEL_PATH",
        os.path.join(_BASE_DIR, "ml", "models", "aqi_model.pkl")
    )
    SCALER_PATH: str = os.getenv(
        "SCALER_PATH",
        os.path.join(_BASE_DIR, "ml", "models", "scaler.pkl")
    )
    FEATURE_NAMES_PATH: str = os.getenv(
        "FEATURE_NAMES_PATH",
        os.path.join(_BASE_DIR, "ml", "models", "feature_names.json")
    )

    # OpenAQ
    OPENAQ_API_KEY: str = os.getenv("OPENAQ_API_KEY", "")
    OPENAQ_BASE_URL: str = os.getenv("OPENAQ_BASE_URL", "https://api.openaq.io/v2")

    # Frontend
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # File upload
    MAX_CONTENT_LENGTH: int = 50 * 1024 * 1024  # 50 MB
    UPLOAD_FOLDER: str = "uploads"
    ALLOWED_EXTENSIONS: set = {"csv", "xlsx", "json"}

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/app.log")

    # Swagger / Flasgger
    SWAGGER_CONFIG: dict = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec",
                "route": "/apispec.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api/docs/",
        "title": "AQI Prediction API",
        "uiversion": 3,
    }

    SWAGGER: dict = {
        "title": "AI AQI Prediction API",
        "uiversion": 3,
        "openapi": "3.0.3",
        "info": {
            "title": "AI-Based AQI Prediction API",
            "description": (
                "Production-ready REST API for AI-Based Air Quality Index "
                "Prediction and Explainable Environmental Analytics."
            ),
            "version": "1.0.0",
            "contact": {"email": "support@aqiprediction.com"},
        },
        "securityDefinitions": {
            "BearerAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
                "description": "JWT Bearer token: 'Bearer <token>'",
            }
        },
    }


class DevelopmentConfig(BaseConfig):
    DEBUG: bool = True
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:password@localhost:3306/aqi_prediction_db",
    )
    SQLALCHEMY_ECHO: bool = True


class TestingConfig(BaseConfig):
    TESTING: bool = True
    DEBUG: bool = True
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"
    WTF_CSRF_ENABLED: bool = False
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(minutes=5)


class ProductionConfig(BaseConfig):
    DEBUG: bool = False
    SQLALCHEMY_DATABASE_URI: str = os.getenv("DATABASE_URL", "")
    SQLALCHEMY_ECHO: bool = False

    # Enforce secure settings
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"
    PREFERRED_URL_SCHEME: str = "https"


config_by_name: dict = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
