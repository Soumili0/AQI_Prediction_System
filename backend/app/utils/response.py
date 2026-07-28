"""
Standardised API Response Helpers
===================================
Use these instead of calling jsonify() directly in routes.
Ensures every response has a consistent envelope structure.

Usage:
    from app.utils.response import success, error, paginated

    return success(data={"user": user.to_dict()}, message="Profile loaded.", code=200)
    return error("Invalid input", code=400)
    return paginated(items, total=100, page=1, per_page=20)
"""

from flask import jsonify
from typing import Any


def success(data: Any = None, message: str = "", code: int = 200):
    """Return a successful JSON response.

    Args:
        data:    dict, list, or any JSON-serialisable value.
        message: Optional human-readable description.
        code:    HTTP status code (default 200).

    Returns:
        (flask.Response, int) tuple.
    """
    body = {"status": "success"}
    if message:
        body["message"] = message
    if data is not None:
        if isinstance(data, dict):
            body.update(data)
        else:
            body["data"] = data
    return jsonify(body), code


def error(message: str, code: int = 400, details: Any = None):
    """Return an error JSON response.

    Args:
        message: Human-readable error description.
        code:    HTTP status code (default 400).
        details: Optional extra details (validation errors, etc.).

    Returns:
        (flask.Response, int) tuple.
    """
    body = {"status": "error", "error": message}
    if details is not None:
        body["details"] = details
    return jsonify(body), code


def paginated(items: list, total: int, page: int, per_page: int,
              item_key: str = "items", extra: dict = None):
    """Return a paginated JSON response.

    Args:
        items:    List of serialised items for the current page.
        total:    Total record count across all pages.
        page:     Current page number (1-based).
        per_page: Items per page.
        item_key: Key name for the items array in the response.
        extra:    Additional fields to merge into the response.

    Returns:
        (flask.Response, int) tuple.
    """
    body = {
        "status": "success",
        item_key: items,
        "pagination": {
            "total":    total,
            "page":     page,
            "per_page": per_page,
            "pages":    max(1, -(-total // per_page)),  # ceiling division
            "has_next": page * per_page < total,
            "has_prev": page > 1,
        },
    }
    if extra:
        body.update(extra)
    return jsonify(body), 200
