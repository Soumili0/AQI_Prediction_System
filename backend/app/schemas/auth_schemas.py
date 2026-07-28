"""
Auth Marshmallow schemas — request body validation for auth endpoints.
"""

import re
from marshmallow import Schema, fields, validate, validates, ValidationError


_PASSWORD_RE = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&_\-#])[A-Za-z\d@$!%*?&_\-#]{8,128}$"
)


class RegisterSchema(Schema):
    """POST /auth/register"""
    email     = fields.Email(required=True, load_default=None)
    username  = fields.Str(
        required=True,
        validate=validate.Regexp(r'^[a-zA-Z0-9_\-]{3,50}$',
                                 error="Username must be 3-50 chars: letters, digits, _ or -")
    )
    password  = fields.Str(required=True, load_default=None)
    first_name= fields.Str(load_default=None, validate=validate.Length(max=100))
    last_name = fields.Str(load_default=None, validate=validate.Length(max=100))
    role      = fields.Str(
        load_default="citizen",
        validate=validate.OneOf(["citizen", "researcher", "policy_maker"])
    )
    organization = fields.Str(load_default=None, validate=validate.Length(max=255))
    city      = fields.Str(load_default=None, validate=validate.Length(max=100))
    country   = fields.Str(load_default=None, validate=validate.Length(max=100))

    @validates("password")
    def validate_password(self, value):
        if not _PASSWORD_RE.match(value):
            raise ValidationError(
                "Password must be 8-128 chars with at least one uppercase, "
                "one lowercase, one digit, and one special character (@$!%*?&_-#)."
            )


class LoginSchema(Schema):
    """POST /auth/login"""
    email    = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=1))


class ForgotPasswordSchema(Schema):
    """POST /auth/forgot-password"""
    email = fields.Email(required=True)


class ResetPasswordSchema(Schema):
    """POST /auth/reset-password"""
    token        = fields.Str(required=True, validate=validate.Length(min=10))
    new_password = fields.Str(required=True)

    @validates("new_password")
    def validate_password(self, value):
        if not _PASSWORD_RE.match(value):
            raise ValidationError(
                "New password must be 8-128 chars with uppercase, lowercase, digit and special char."
            )


class ChangePasswordSchema(Schema):
    """PUT /auth/me/change-password"""
    current_password = fields.Str(required=True, validate=validate.Length(min=1))
    new_password     = fields.Str(required=True)

    @validates("new_password")
    def validate_password(self, value):
        if not _PASSWORD_RE.match(value):
            raise ValidationError("New password does not meet strength requirements.")
