"""
Authentication Service
======================
Contains all business logic for user authentication:
  - register          : create account, send verification email
  - login             : validate credentials, issue JWT pair
  - refresh           : rotate access token using refresh token
  - logout            : revoke refresh token
  - verify_email      : confirm email ownership
  - forgot_password   : generate reset token, send email
  - reset_password    : consume reset token, update password
  - get_profile       : return current user data
  - update_profile    : update non-sensitive fields

Raises ValueError for business-rule violations (caught and turned into
HTTP 400/401/404 responses by the route layer).
"""

import secrets
from datetime import datetime, timedelta

from flask import current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    decode_token,
)

from app import db
from app.models.user import User
from app.models.role import Role
from app.models.refresh_token import RefreshToken
from app.utils.audit import log_action
from app.utils.email_utils import send_verification_email, send_password_reset_email
from app.utils.validators import validate_email, validate_password, validate_username


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register_user(data: dict) -> dict:
    """Create a new user account.

    Args:
        data: dict with keys: email, username, password, first_name,
              last_name, role (optional), organization, city, country.

    Returns:
        dict with 'user' and 'message' keys.

    Raises:
        ValueError: on validation failure or duplicate email/username.
    """
    email = (data.get("email") or "").strip().lower()
    username = (data.get("username") or "").strip()
    password = data.get("password", "")
    role_name = (data.get("role") or "citizen").strip().lower()

    # --- Validation ---
    for err in [validate_email(email), validate_username(username), validate_password(password)]:
        if err:
            raise ValueError(err)

    # Only admin can assign non-citizen roles via API
    allowed_self_roles = {"citizen", "researcher", "policy_maker"}
    if role_name not in allowed_self_roles:
        role_name = "citizen"

    if User.query.filter_by(email=email).first():
        raise ValueError("An account with this email already exists.")
    if User.query.filter_by(username=username).first():
        raise ValueError("This username is already taken.")

    role = Role.query.filter_by(name=role_name).first()
    if not role:
        role = Role.query.filter_by(name="citizen").first()

    verify_token = secrets.token_urlsafe(48)

    user = User(
        email=email,
        username=username,
        first_name=(data.get("first_name") or "").strip() or None,
        last_name=(data.get("last_name") or "").strip() or None,
        organization=(data.get("organization") or "").strip() or None,
        city=(data.get("city") or "").strip() or None,
        country=(data.get("country") or "").strip() or None,
        role_id=role.id,
        verify_token=verify_token,
        is_verified=False,
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    # Send verification email (non-blocking; log error if it fails)
    try:
        send_verification_email(
            recipient_email=email,
            recipient_name=user.first_name or user.username,
            verify_token=verify_token,
        )
    except Exception as exc:
        current_app.logger.warning("Verification email failed: %s", exc)

    log_action("user.register", entity="users", entity_id=user.id,
               new_value={"email": email, "role": role_name}, user_id=user.id)

    return {
        "user": user.to_dict(),
        "message": "Registration successful. Please check your email to verify your account.",
    }


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def login_user(email: str, password: str) -> dict:
    """Authenticate user and issue JWT access + refresh tokens.

    Returns:
        dict with access_token, refresh_token, user.

    Raises:
        ValueError: on invalid credentials or inactive account.
    """
    email = (email or "").strip().lower()

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        log_action("user.login_failed", entity="users",
                   new_value={"email": email}, status="failure")
        raise ValueError("Invalid email or password.")

    if not user.is_active:
        raise ValueError("Your account has been deactivated. Please contact support.")

    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()

    access_token = create_access_token(identity=user.id)
    refresh_token_str = create_refresh_token(identity=user.id)

    # Persist refresh token for revocation support
    decoded = decode_token(refresh_token_str)
    expires_at = datetime.utcfromtimestamp(decoded["exp"])
    rt = RefreshToken(user_id=user.id, jti=decoded["jti"], expires_at=expires_at)
    db.session.add(rt)
    db.session.commit()

    log_action("user.login", entity="users", entity_id=user.id, user_id=user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "Bearer",
        "user": user.to_dict(),
    }


# ---------------------------------------------------------------------------
# Token Refresh
# ---------------------------------------------------------------------------

def refresh_access_token(jti: str, user_id: int) -> dict:
    """Issue a new access token if the refresh token is valid and not revoked.

    Args:
        jti:     JWT ID from the decoded refresh token.
        user_id: Identity from the decoded refresh token.

    Returns:
        dict with new access_token.

    Raises:
        ValueError: if token is revoked or not found.
    """
    token_record = RefreshToken.query.filter_by(jti=jti, user_id=user_id).first()

    if not token_record or not token_record.is_valid():
        raise ValueError("Refresh token is invalid or has been revoked.")

    user = User.query.get(user_id)
    if not user or not user.is_active:
        raise ValueError("User not found or account is deactivated.")

    new_access_token = create_access_token(identity=user_id)
    return {"access_token": new_access_token, "token_type": "Bearer"}


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

def logout_user(jti: str) -> None:
    """Revoke the refresh token so it cannot be used again."""
    token_record = RefreshToken.query.filter_by(jti=jti).first()
    if token_record:
        token_record.revoke()
        db.session.commit()


# ---------------------------------------------------------------------------
# Email Verification
# ---------------------------------------------------------------------------

def verify_email(token: str) -> dict:
    """Mark the user's email as verified.

    Raises:
        ValueError: if the token is invalid or already used.
    """
    if not token:
        raise ValueError("Verification token is required.")

    user = User.query.filter_by(verify_token=token).first()
    if not user:
        raise ValueError("Invalid or expired verification token.")

    if user.is_verified:
        return {"message": "Email is already verified."}

    user.is_verified = True
    user.verify_token = None
    db.session.commit()

    log_action("user.verify_email", entity="users", entity_id=user.id, user_id=user.id)
    return {"message": "Email verified successfully. You can now log in."}


# ---------------------------------------------------------------------------
# Forgot Password
# ---------------------------------------------------------------------------

def forgot_password(email: str) -> dict:
    """Generate a reset token and send reset email.

    Always returns a success-like message to prevent user enumeration.
    """
    email = (email or "").strip().lower()
    message = "If that email is registered, you will receive a password reset link shortly."

    user = User.query.filter_by(email=email).first()
    if not user or not user.is_active:
        # Return generic message — do NOT reveal whether email exists
        return {"message": message}

    reset_token = secrets.token_urlsafe(48)
    user.password_reset_token = reset_token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    db.session.commit()

    try:
        send_password_reset_email(
            recipient_email=email,
            recipient_name=user.first_name or user.username,
            reset_token=reset_token,
        )
    except Exception as exc:
        current_app.logger.error("Password reset email failed: %s", exc)

    log_action("user.forgot_password", entity="users", entity_id=user.id, user_id=user.id)
    return {"message": message}


# ---------------------------------------------------------------------------
# Reset Password
# ---------------------------------------------------------------------------

def reset_password(token: str, new_password: str) -> dict:
    """Consume the reset token and update the password.

    Raises:
        ValueError: if token is invalid/expired or password is weak.
    """
    if not token:
        raise ValueError("Reset token is required.")

    err = validate_password(new_password)
    if err:
        raise ValueError(err)

    user = User.query.filter_by(password_reset_token=token).first()
    if not user:
        raise ValueError("Invalid or expired reset token.")

    if user.reset_token_expires < datetime.utcnow():
        raise ValueError("Reset token has expired. Please request a new one.")

    user.set_password(new_password)
    user.password_reset_token = None
    user.reset_token_expires = None
    db.session.commit()

    # Revoke all existing refresh tokens for this user
    RefreshToken.query.filter_by(user_id=user.id).update({"is_revoked": True})
    db.session.commit()

    log_action("user.reset_password", entity="users", entity_id=user.id, user_id=user.id)
    return {"message": "Password reset successfully. Please log in with your new password."}


# ---------------------------------------------------------------------------
# Profile Management
# ---------------------------------------------------------------------------

def get_user_profile(user_id: int) -> dict:
    """Return full profile data for the current user."""
    user = User.query.get(user_id)
    if not user:
        raise ValueError("User not found.")
    return user.to_dict(include_private=True)


def update_user_profile(user_id: int, data: dict) -> dict:
    """Update non-sensitive profile fields.

    Raises:
        ValueError: on validation errors or duplicate username.
    """
    user = User.query.get(user_id)
    if not user:
        raise ValueError("User not found.")

    updatable_fields = ["first_name", "last_name", "phone", "organization", "city", "country", "avatar_url"]

    if "username" in data:
        new_username = data["username"].strip()
        err = validate_username(new_username)
        if err:
            raise ValueError(err)
        existing = User.query.filter_by(username=new_username).first()
        if existing and existing.id != user_id:
            raise ValueError("Username is already taken.")
        user.username = new_username

    for field in updatable_fields:
        if field in data:
            setattr(user, field, (data[field] or "").strip() or None)

    db.session.commit()
    log_action("user.update_profile", entity="users", entity_id=user.id, user_id=user.id)
    return user.to_dict(include_private=True)


def change_password(user_id: int, current_password: str, new_password: str) -> dict:
    """Authenticated password change (requires current password).

    Raises:
        ValueError: on wrong current password or weak new password.
    """
    user = User.query.get(user_id)
    if not user:
        raise ValueError("User not found.")

    if not user.check_password(current_password):
        raise ValueError("Current password is incorrect.")

    err = validate_password(new_password)
    if err:
        raise ValueError(err)

    user.set_password(new_password)
    db.session.commit()

    # Revoke all refresh tokens → forces re-login on other devices
    RefreshToken.query.filter_by(user_id=user_id).update({"is_revoked": True})
    db.session.commit()

    log_action("user.change_password", entity="users", entity_id=user_id, user_id=user_id)
    return {"message": "Password changed successfully. Please log in again on other devices."}
