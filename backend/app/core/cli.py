"""
Flask CLI Commands
==================
Custom management commands registered on the Flask app.

Usage:
  flask seed-db          — insert roles + default admin user
  flask create-admin     — interactively create an admin account
  flask list-routes      — print all registered URL rules
  flask db-status        — show table row counts
  flask purge-tokens     — delete expired refresh tokens
"""

import click
from flask import current_app
from flask.cli import with_appcontext


def register_commands(app):
    """Attach all CLI commands to the app."""
    app.cli.add_command(seed_db)
    app.cli.add_command(create_admin)
    app.cli.add_command(list_routes)
    app.cli.add_command(db_status)
    app.cli.add_command(purge_tokens)


# ---------------------------------------------------------------------------
# seed-db
# ---------------------------------------------------------------------------
@click.command("seed-db")
@with_appcontext
def seed_db():
    """Seed the database with roles and a default admin user."""
    from app import db
    from app.models.role import Role
    from app.models.user import User

    click.echo("Seeding roles…")
    roles = [
        ("admin",        "Full system access"),
        ("researcher",   "Research and model access"),
        ("policy_maker", "Read-only analytics"),
        ("citizen",      "Public prediction access"),
    ]
    for name, desc in roles:
        if not Role.query.filter_by(name=name).first():
            db.session.add(Role(name=name, description=desc))
            click.echo(f"  + role: {name}")
        else:
            click.echo(f"  ✓ role already exists: {name}")

    db.session.commit()

    click.echo("\nChecking default admin…")
    admin_email = "admin@aqisystem.local"
    if not User.query.filter_by(email=admin_email).first():
        role = Role.query.filter_by(name="admin").first()
        admin = User(
            email=admin_email,
            username="sysadmin",
            first_name="System",
            last_name="Admin",
            role_id=role.id,
            is_active=True,
            is_verified=True,
        )
        admin.set_password("Admin@12345")
        db.session.add(admin)
        db.session.commit()
        click.echo(f"  + Default admin created: {admin_email}  password: Admin@12345")
        click.echo("  ⚠  Change the default password immediately!")
    else:
        click.echo(f"  ✓ Admin already exists: {admin_email}")

    click.echo("\nDatabase seeding complete ✓")


# ---------------------------------------------------------------------------
# create-admin
# ---------------------------------------------------------------------------
@click.command("create-admin")
@with_appcontext
def create_admin():
    """Interactively create a new admin user."""
    from app import db
    from app.models.role import Role
    from app.models.user import User
    from app.utils.validators import validate_email, validate_password, validate_username

    click.echo("Create Admin User")
    click.echo("─" * 30)

    email    = click.prompt("Email")
    username = click.prompt("Username")
    password = click.prompt("Password", hide_input=True, confirmation_prompt=True)

    # Validate
    for err in [validate_email(email), validate_username(username), validate_password(password)]:
        if err:
            click.echo(f"Error: {err}", err=True)
            return

    if User.query.filter_by(email=email).first():
        click.echo("Error: Email already exists.", err=True)
        return
    if User.query.filter_by(username=username).first():
        click.echo("Error: Username already taken.", err=True)
        return

    role = Role.query.filter_by(name="admin").first()
    if not role:
        click.echo("Error: Admin role not found. Run `flask seed-db` first.", err=True)
        return

    user = User(
        email=email.strip().lower(),
        username=username.strip(),
        first_name=click.prompt("First name", default=""),
        last_name=click.prompt("Last name",  default=""),
        role_id=role.id,
        is_active=True,
        is_verified=True,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    click.echo(f"\n✓ Admin user created: {email} (id={user.id})")


# ---------------------------------------------------------------------------
# list-routes
# ---------------------------------------------------------------------------
@click.command("list-routes")
@with_appcontext
def list_routes():
    """Print all registered URL rules with methods."""
    from flask import current_app
    rules = sorted(current_app.url_map.iter_rules(), key=lambda r: r.rule)
    click.echo(f"\n{'Method':<15} {'Endpoint':<45} {'Rule'}")
    click.echo("─" * 90)
    for rule in rules:
        methods = ",".join(sorted(rule.methods - {"HEAD", "OPTIONS"}))
        click.echo(f"{methods:<15} {rule.endpoint:<45} {rule.rule}")
    click.echo(f"\nTotal: {len(rules)} routes")


# ---------------------------------------------------------------------------
# db-status
# ---------------------------------------------------------------------------
@click.command("db-status")
@with_appcontext
def db_status():
    """Show row counts for all main tables."""
    from app import db
    from app.models.user import User
    from app.models.prediction import Prediction
    from app.models.dataset import Dataset
    from app.models.aqi_reading import AQIReading
    from app.models.ml_model import MLModel
    from app.models.audit_log import AuditLog

    click.echo("\nDatabase Status")
    click.echo("─" * 30)
    tables = [
        ("users",        User),
        ("predictions",  Prediction),
        ("datasets",     Dataset),
        ("aqi_readings", AQIReading),
        ("ml_models",    MLModel),
        ("audit_logs",   AuditLog),
    ]
    for name, model in tables:
        count = model.query.count()
        click.echo(f"  {name:<20} {count:>8,} rows")


# ---------------------------------------------------------------------------
# purge-tokens
# ---------------------------------------------------------------------------
@click.command("purge-tokens")
@with_appcontext
def purge_tokens():
    """Delete expired and revoked refresh tokens to keep the table clean."""
    from datetime import datetime
    from app import db
    from app.models.refresh_token import RefreshToken

    deleted = (
        RefreshToken.query
        .filter(
            (RefreshToken.expires_at < datetime.utcnow()) |
            (RefreshToken.is_revoked == True)
        )
        .delete(synchronize_session=False)
    )
    db.session.commit()
    click.echo(f"Purged {deleted:,} expired/revoked token(s).")
