"""
Input Validators
================
Reusable validation helpers used across schemas and service layers.
"""

import re
from typing import Optional


# Minimum password requirements
_PASSWORD_REGEX = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&_\-#])[A-Za-z\d@$!%*?&_\-#]{8,128}$"
)
_EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
_USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_\-]{3,50}$")


def validate_email(email: str) -> Optional[str]:
    """Return error message or None if valid."""
    if not email or not email.strip():
        return "Email is required."
    if not _EMAIL_REGEX.match(email.strip()):
        return "Invalid email format."
    return None


def validate_password(password: str) -> Optional[str]:
    """Enforce strong password policy."""
    if not password:
        return "Password is required."
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if len(password) > 128:
        return "Password must not exceed 128 characters."
    if not _PASSWORD_REGEX.match(password):
        return (
            "Password must contain at least one uppercase letter, "
            "one lowercase letter, one digit, and one special character (@$!%*?&_-#)."
        )
    return None


def validate_username(username: str) -> Optional[str]:
    """Validate username format."""
    if not username or not username.strip():
        return "Username is required."
    if not _USERNAME_REGEX.match(username.strip()):
        return "Username must be 3-50 characters and contain only letters, digits, underscores, or hyphens."
    return None


def sanitize_string(value: str, max_length: int = 255) -> str:
    """Strip whitespace and truncate to max_length."""
    if not value:
        return ""
    return value.strip()[:max_length]
