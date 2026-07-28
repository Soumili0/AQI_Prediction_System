"""
Email Utilities
===============
Sends transactional emails (verification, password reset) using Flask-Mail.
All email bodies are plain-text for maximum deliverability plus an HTML
fallback. Templates are kept inline to avoid a separate template directory
dependency.
"""

from flask import current_app
from flask_mail import Message
from app import mail


def send_password_reset_email(recipient_email: str, recipient_name: str, reset_token: str) -> None:
    """Send a password reset link to the user.

    Args:
        recipient_email: User's registered email address.
        recipient_name:  User's display name.
        reset_token:     Signed, time-limited reset token.
    """
    frontend_url = current_app.config.get("FRONTEND_URL", "http://localhost:5173")
    reset_link = f"{frontend_url}/reset-password?token={reset_token}"

    subject = "Reset Your AQI Prediction Password"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
      <div style="background: linear-gradient(135deg, #1e3a5f, #2d6a4f); padding: 30px; border-radius: 8px 8px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 24px;">🌍 AQI Prediction System</h1>
      </div>
      <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; border: 1px solid #ddd;">
        <h2 style="color: #1e3a5f;">Password Reset Request</h2>
        <p>Hello <strong>{recipient_name}</strong>,</p>
        <p>We received a request to reset the password for your account. Click the button below to reset it:</p>
        <div style="text-align: center; margin: 30px 0;">
          <a href="{reset_link}"
             style="background-color: #2d6a4f; color: white; padding: 14px 28px;
                    text-decoration: none; border-radius: 6px; font-size: 16px;
                    display: inline-block;">
            Reset Password
          </a>
        </div>
        <p style="color: #666; font-size: 14px;">
          This link will expire in <strong>1 hour</strong>. If you did not request a password reset,
          please ignore this email — your password will remain unchanged.
        </p>
        <p style="color: #666; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 15px;">
          If the button doesn't work, copy and paste this URL into your browser:<br>
          <a href="{reset_link}" style="color: #2d6a4f;">{reset_link}</a>
        </p>
      </div>
    </body>
    </html>
    """

    text_body = (
        f"Hello {recipient_name},\n\n"
        f"Reset your AQI Prediction password using this link (expires in 1 hour):\n\n"
        f"{reset_link}\n\n"
        f"If you did not request this, ignore this email.\n\n"
        f"— AQI Prediction Team"
    )

    _send_email(subject=subject, recipients=[recipient_email],
                text_body=text_body, html_body=html_body)


def send_verification_email(recipient_email: str, recipient_name: str, verify_token: str) -> None:
    """Send an email verification link to a newly registered user."""
    frontend_url = current_app.config.get("FRONTEND_URL", "http://localhost:5173")
    verify_link = f"{frontend_url}/verify-email?token={verify_token}"

    subject = "Verify Your Email — AQI Prediction System"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
      <div style="background: linear-gradient(135deg, #1e3a5f, #2d6a4f); padding: 30px; border-radius: 8px 8px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 24px;">🌍 AQI Prediction System</h1>
      </div>
      <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; border: 1px solid #ddd;">
        <h2 style="color: #1e3a5f;">Welcome, {recipient_name}!</h2>
        <p>Thank you for registering. Please verify your email address to activate your account:</p>
        <div style="text-align: center; margin: 30px 0;">
          <a href="{verify_link}"
             style="background-color: #1e3a5f; color: white; padding: 14px 28px;
                    text-decoration: none; border-radius: 6px; font-size: 16px;
                    display: inline-block;">
            Verify Email
          </a>
        </div>
        <p style="color: #666; font-size: 14px;">This link expires in <strong>24 hours</strong>.</p>
      </div>
    </body>
    </html>
    """

    text_body = (
        f"Welcome {recipient_name}!\n\n"
        f"Verify your email using this link (expires in 24 hours):\n\n"
        f"{verify_link}\n\n"
        f"— AQI Prediction Team"
    )

    _send_email(subject=subject, recipients=[recipient_email],
                text_body=text_body, html_body=html_body)


def _send_email(subject: str, recipients: list, text_body: str, html_body: str) -> None:
    """Internal helper to send an email via Flask-Mail."""
    msg = Message(
        subject=subject,
        recipients=recipients,
        body=text_body,
        html=html_body,
        sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
    )
    try:
        mail.send(msg)
        current_app.logger.info("Email sent to %s: %s", recipients, subject)
    except Exception as exc:
        current_app.logger.error("Failed to send email to %s: %s", recipients, exc)
        raise
