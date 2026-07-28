"""Unit tests — SQLAlchemy models"""

import pytest
from app.models.user import User
from app.models.role import Role
from app.models.prediction import get_aqi_category


class TestUserModel:
    def test_password_hashing(self, app):
        with app.app_context():
            user = User(email="hash@test.com", username="hashtest")
            user.set_password("MyPass@123")
            assert user.password_hash != "MyPass@123"
            assert user.check_password("MyPass@123") is True
            assert user.check_password("WrongPass@1") is False

    def test_role_name_default(self, app, db):
        with app.app_context():
            role = Role.query.filter_by(name="citizen").first()
            user = User(email="role@test.com", username="roletest", role_id=role.id)
            db.session.add(user)
            db.session.commit()
            assert user.role_name == "citizen"

    def test_has_role(self, app, db):
        with app.app_context():
            role = Role.query.filter_by(name="citizen").first()
            user = User(email="hasrole@test.com", username="hasroletest", role_id=role.id)
            db.session.add(user)
            db.session.commit()
            assert user.has_role("citizen") is True
            assert user.has_role("admin") is False

    def test_is_admin_false_for_citizen(self, app, db):
        with app.app_context():
            role = Role.query.filter_by(name="citizen").first()
            user = User(email="notadmin@test.com", username="notadmin", role_id=role.id)
            db.session.add(user)
            db.session.commit()
            assert user.is_admin() is False

    def test_to_dict(self, app, db):
        with app.app_context():
            role = Role.query.filter_by(name="citizen").first()
            user = User(email="dict@test.com", username="dicttest",
                        first_name="Dict", role_id=role.id, is_active=True)
            db.session.add(user)
            db.session.commit()
            d = user.to_dict()
            assert d["email"] == "dict@test.com"
            assert d["username"] == "dicttest"
            assert "password_hash" not in d


class TestAQICategory:
    @pytest.mark.parametrize("aqi,expected_cat", [
        (25,   "Good"),
        (75,   "Moderate"),
        (125,  "Unhealthy for Sensitive Groups"),
        (175,  "Unhealthy"),
        (250,  "Very Unhealthy"),
        (400,  "Hazardous"),
    ])
    def test_category_ranges(self, aqi, expected_cat):
        cat, advisory = get_aqi_category(aqi)
        assert cat == expected_cat
        assert advisory  # non-empty advisory

    def test_boundary_good(self):
        cat, _ = get_aqi_category(50)
        assert cat == "Good"

    def test_boundary_moderate(self):
        cat, _ = get_aqi_category(51)
        assert cat == "Moderate"
