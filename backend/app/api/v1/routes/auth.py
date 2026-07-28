"""
Authentication Routes
=====================
All endpoints under /api/v1/auth/

POST   /register          — create new account
POST   /login             — issue JWT pair
POST   /refresh           — rotate access token
POST   /logout            — revoke refresh token
POST   /verify-email      — confirm email address
POST   /forgot-password   — request reset link
POST   /reset-password    — set new password with token
GET    /me                — get current user profile
PUT    /me                — update profile
PUT    /me/change-password — authenticated password change
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    get_jwt,
    verify_jwt_in_request,
)

from app import limiter
from app.services import auth_service

auth_bp = Blueprint("auth", __name__)


# ---------------------------------------------------------------------------
# POST /register
# ---------------------------------------------------------------------------
@auth_bp.post("/register")
@limiter.limit("10 per hour")
def register():
    """
    Register a new user account.
    ---
    tags:
      - Authentication
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [email, username, password]
            properties:
              email:        { type: string, example: "user@example.com" }
              username:     { type: string, example: "john_doe" }
              password:     { type: string, example: "SecurePass@1" }
              first_name:   { type: string, example: "John" }
              last_name:    { type: string, example: "Doe" }
              role:         { type: string, enum: [citizen, researcher, policy_maker] }
              organization: { type: string }
              city:         { type: string }
              country:      { type: string }
    responses:
      201:
        description: Registration successful
      400:
        description: Validation error
      409:
        description: Email or username already exists
    """
    data = request.get_json(silent=True) or {}
    try:
        result = auth_service.register_user(data)
        return jsonify(result), 201
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


# ---------------------------------------------------------------------------
# POST /login
# ---------------------------------------------------------------------------
@auth_bp.post("/login")
@limiter.limit("20 per hour")
def login():
    """
    Authenticate and receive JWT tokens.
    ---
    tags:
      - Authentication
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [email, password]
            properties:
              email:    { type: string }
              password: { type: string }
    responses:
      200:
        description: Login successful; returns access_token and refresh_token
      401:
        description: Invalid credentials
    """
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    try:
        result = auth_service.login_user(email, password)
        return jsonify(result), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 401


# ---------------------------------------------------------------------------
# POST /refresh
# ---------------------------------------------------------------------------
@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    """
    Issue a new access token using a valid refresh token.
    ---
    tags:
      - Authentication
    security:
      - BearerAuth: []
    responses:
      200:
        description: New access token
      401:
        description: Invalid or revoked refresh token
    """
    user_id = get_jwt_identity()
    jti = get_jwt()["jti"]

    try:
        result = auth_service.refresh_access_token(jti=jti, user_id=user_id)
        return jsonify(result), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 401


# ---------------------------------------------------------------------------
# POST /logout
# ---------------------------------------------------------------------------
@auth_bp.post("/logout")
@jwt_required(refresh=True)
def logout():
    """
    Revoke the current refresh token.
    ---
    tags:
      - Authentication
    security:
      - BearerAuth: []
    responses:
      200:
        description: Logout successful
    """
    jti = get_jwt()["jti"]
    auth_service.logout_user(jti)
    return jsonify({"message": "Logged out successfully."}), 200


# ---------------------------------------------------------------------------
# POST /verify-email
# ---------------------------------------------------------------------------
@auth_bp.post("/verify-email")
def verify_email():
    """
    Verify user email with token sent during registration.
    ---
    tags:
      - Authentication
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [token]
            properties:
              token: { type: string }
    responses:
      200:
        description: Email verified
      400:
        description: Invalid or expired token
    """
    data = request.get_json(silent=True) or {}
    token = data.get("token", "")
    try:
        result = auth_service.verify_email(token)
        return jsonify(result), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


# ---------------------------------------------------------------------------
# POST /forgot-password
# ---------------------------------------------------------------------------
@auth_bp.post("/forgot-password")
@limiter.limit("5 per hour")
def forgot_password():
    """
    Request a password reset link via email.
    ---
    tags:
      - Authentication
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [email]
            properties:
              email: { type: string }
    responses:
      200:
        description: Reset email sent (always 200 to prevent enumeration)
    """
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    result = auth_service.forgot_password(email)
    return jsonify(result), 200


# ---------------------------------------------------------------------------
# POST /reset-password
# ---------------------------------------------------------------------------
@auth_bp.post("/reset-password")
@limiter.limit("10 per hour")
def reset_password():
    """
    Reset password using the emailed token.
    ---
    tags:
      - Authentication
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [token, new_password]
            properties:
              token:        { type: string }
              new_password: { type: string }
    responses:
      200:
        description: Password reset successful
      400:
        description: Invalid token or weak password
    """
    data = request.get_json(silent=True) or {}
    token = data.get("token", "")
    new_password = data.get("new_password", "")

    try:
        result = auth_service.reset_password(token, new_password)
        return jsonify(result), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


# ---------------------------------------------------------------------------
# GET /me
# ---------------------------------------------------------------------------
@auth_bp.get("/me")
@jwt_required()
def get_profile():
    """
    Get the current authenticated user's profile.
    ---
    tags:
      - Authentication
    security:
      - BearerAuth: []
    responses:
      200:
        description: User profile data
      401:
        description: Unauthorized
    """
    user_id = get_jwt_identity()
    try:
        profile = auth_service.get_user_profile(user_id)
        return jsonify({"user": profile}), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404


# ---------------------------------------------------------------------------
# PUT /me
# ---------------------------------------------------------------------------
@auth_bp.put("/me")
@jwt_required()
def update_profile():
    """
    Update the current user's profile information.
    ---
    tags:
      - Authentication
    security:
      - BearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              username:     { type: string }
              first_name:   { type: string }
              last_name:    { type: string }
              phone:        { type: string }
              organization: { type: string }
              city:         { type: string }
              country:      { type: string }
              avatar_url:   { type: string }
    responses:
      200:
        description: Profile updated
      400:
        description: Validation error
    """
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    try:
        result = auth_service.update_user_profile(user_id, data)
        return jsonify({"user": result, "message": "Profile updated successfully."}), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


# ---------------------------------------------------------------------------
# PUT /me/change-password
# ---------------------------------------------------------------------------
@auth_bp.put("/me/change-password")
@jwt_required()
def change_password():
    """
    Change password (requires current password).
    ---
    tags:
      - Authentication
    security:
      - BearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [current_password, new_password]
            properties:
              current_password: { type: string }
              new_password:     { type: string }
    responses:
      200:
        description: Password changed
      400:
        description: Incorrect current password or weak new password
    """
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    current_pw = data.get("current_password", "")
    new_pw = data.get("new_password", "")

    if not current_pw or not new_pw:
        return jsonify({"error": "Both current_password and new_password are required."}), 400

    try:
        result = auth_service.change_password(user_id, current_pw, new_pw)
        return jsonify(result), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
