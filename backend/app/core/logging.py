"""
Structured Logging Setup
========================
Configures Python's built-in logging plus structlog for JSON output in
production and pretty console output in development.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from flask import Flask


def setup_logging(app: Flask) -> None:
    """Configure application-wide logging.

    - Development: human-readable console output at DEBUG level.
    - Production:  JSON-formatted rotating file + console at INFO level.
    """
    log_level_str = app.config.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    log_file = app.config.get("LOG_FILE", "logs/app.log")

    # Ensure log directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s (%(funcName)s:%(lineno)d): %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # Rotating file handler (10 MB × 5 backups)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # Apply to root logger and Flask's logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    app.logger.setLevel(log_level)

    # Suppress noisy libraries in production
    if not app.debug:
        for noisy in ("werkzeug", "urllib3", "sqlalchemy.engine"):
            logging.getLogger(noisy).setLevel(logging.WARNING)

    app.logger.info("Logging configured at level %s → %s", log_level_str, log_file)
