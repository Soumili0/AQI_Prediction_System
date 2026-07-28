"""
Pytest configuration and shared fixtures
=========================================
Uses SQLite in-memory DB for speed.
Every test gets a fresh DB transaction rolled back on teardown.
"""

import pytest
from app import create_app, db as _db
from app.models.role import Role
from app.models.user import User


@pytest.fixture(scope="session")
def app():
    """Create application for the test session."""
    app = create_app("testing")
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-jwt-secret",
        "WTF_CSRF_ENABLED": False,
        "MAIL_SUPPRESS_SEND": True,
    })

    with app.app_context():
        _db.create_all()
        _seed_roles()
        yield app
        _db.drop_all()


@pytest.fixture(scope="function")
def db(app):
    """Wrap each test in a transaction and roll back afterwards."""
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()
        _db.session.bind = connection
        yield _db
        transaction.rollback()
        connection.close()
        _db.session.remove()


@pytest.fixture(scope="function")
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture(scope="function")
def citizen_user(db):
    """Create and return a citizen user."""
    role = Role.query.filter_by(name="citizen").first()
    user = User(
        email="citizen@test.com",
        username="citizen_test",
        role_id=role.id,
        is_active=True,
        is_verified=True,
    )
    user.set_password("TestPass@1")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture(scope="function")
def admin_user(db):
    """Create and return an admin user."""
    role = Role.query.filter_by(name="admin").first()
    user = User(
        email="admin@test.com",
        username="admin_test",
        role_id=role.id,
        is_active=True,
        is_verified=True,
    )
    user.set_password("AdminPass@1")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture(scope="function")
def citizen_token(client, citizen_user):
    """JWT access token for the citizen user."""
    resp = client.post("/api/v1/auth/login", json={
        "email": "citizen@test.com",
        "password": "TestPass@1",
    })
    return resp.get_json()["access_token"]


@pytest.fixture(scope="function")
def admin_token(client, admin_user):
    """JWT access token for the admin user."""
    resp = client.post("/api/v1/auth/login", json={
        "email": "admin@test.com",
        "password": "AdminPass@1",
    })
    return resp.get_json()["access_token"]


def _seed_roles():
    """Seed the four application roles."""
    for name, desc in [
        ("admin",        "Full system access"),
        ("researcher",   "Research and model access"),
        ("policy_maker", "Read-only analytics"),
        ("citizen",      "Public prediction access"),
    ]:
        if not Role.query.filter_by(name=name).first():
            _db.session.add(Role(name=name, description=desc))
    _db.session.commit()
