"""
Audit Log Utility
=================
Centralised helper to write immutable audit trail records.
Call `log_action(...)` from anywhere in the application.
"""

from flask import request
from app import db
from app.models.audit_log import AuditLog


def log_action(
    action: str,
    entity: str = None,
    entity_id: str = None,
    old_value: dict = None,
    new_value: dict = None,
    user_id: int = None,
    status: str = "success",
) -> AuditLog:
    """Create and persist an audit log entry.

    Args:
        action:    Short verb describing what happened (e.g. 'user.login').
        entity:    The resource type affected (e.g. 'users', 'predictions').
        entity_id: Primary key of the affected record as a string.
        old_value: JSON-serialisable dict of the previous state.
        new_value: JSON-serialisable dict of the new state.
        user_id:   ID of the user who triggered the action.
        status:    'success' or 'failure'.

    Returns:
        The persisted AuditLog instance.
    """
    try:
        ip = _get_client_ip()
        ua = request.headers.get("User-Agent", "")[:512]
    except RuntimeError:
        # Outside request context (e.g. CLI or tests)
        ip = None
        ua = None

    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=str(entity_id) if entity_id is not None else None,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip,
        user_agent=ua,
        status=status,
    )
    db.session.add(entry)
    db.session.commit()
    return entry


def _get_client_ip() -> str:
    """Extract the real client IP, respecting X-Forwarded-For headers."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr or "unknown"
