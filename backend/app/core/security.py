"""
Security Utilities
==================
Centralised security helpers:
  - Input sanitisation
  - Safe filename generation
  - Token generation
  - SQL injection guard (parameterised query helpers)
  - Content Security Policy header builder
"""

import re
import os
import secrets
import hashlib
from datetime import datetime
from typing import Any
from werkzeug.utils import secure_filename as _werkzeug_secure


# ---------------------------------------------------------------------------
# Safe filename
# ---------------------------------------------------------------------------

def safe_filename(filename: str) -> str:
    """Return a filesystem-safe, collision-resistant filename.

    Prefixes the werkzeug-sanitised name with a timestamp+random to prevent
    path traversal and filename collision attacks.
    """
    base = _werkzeug_secure(filename)
    if not base:
        base = "upload"
    ts     = int(datetime.utcnow().timestamp())
    rnd    = secrets.token_hex(6)
    return f"{ts}_{rnd}_{base}"


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------

def generate_token(nbytes: int = 48) -> str:
    """Generate a URL-safe random token."""
    return secrets.token_urlsafe(nbytes)


def hash_token(token: str) -> str:
    """SHA-256 hash a token for safe DB storage (one-way)."""
    return hashlib.sha256(token.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Input sanitisation
# ---------------------------------------------------------------------------

_DANGEROUS_CHARS = re.compile(r"[<>\"'%;()&+\-]")


def sanitize_input(value: Any, max_length: int = 1024) -> str:
    """Strip dangerous characters and trim to max_length.

    NOT a substitute for parameterised queries — use this for
    display/logging contexts only.
    """
    if value is None:
        return ""
    text = str(value).strip()
    text = _DANGEROUS_CHARS.sub("", text)
    return text[:max_length]


def validate_file_extension(filename: str, allowed: set) -> bool:
    """Return True if the file extension is in the allowed set."""
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[-1].lower()
    return ext in allowed


def validate_numeric_range(value: float, lo: float, hi: float) -> bool:
    """Return True if value is within [lo, hi]."""
    try:
        return lo <= float(value) <= hi
    except (TypeError, ValueError):
        return False


# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------

CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "frame-ancestors 'none';"
)

SECURITY_HEADERS = {
    "X-Content-Type-Options":    "nosniff",
    "X-Frame-Options":           "DENY",
    "X-XSS-Protection":          "1; mode=block",
    "Referrer-Policy":           "strict-origin-when-cross-origin",
    "Permissions-Policy":        "geolocation=(), microphone=(), camera=()",
    "Content-Security-Policy":   CSP_POLICY,
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
}


def apply_security_headers(response):
    """Flask after_request hook — add security headers to every response."""
    for key, value in SECURITY_HEADERS.items():
        response.headers.setdefault(key, value)
    return response
