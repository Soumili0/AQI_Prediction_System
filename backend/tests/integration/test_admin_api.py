"""Integration tests — Admin API endpoints (RBAC enforcement)"""

BASE = "/api/v1/admin"


class TestAdminRBAC:
    def test_stats_requires_auth(self, client):
        resp = client.get(f"{BASE}/stats")
        assert resp.status_code == 401

    def test_stats_forbidden_for_citizen(self, client, citizen_token):
        resp = client.get(f"{BASE}/stats",
                          headers={"Authorization": f"Bearer {citizen_token}"})
        assert resp.status_code == 403

    def test_stats_accessible_for_admin(self, client, admin_token):
        resp = client.get(f"{BASE}/stats",
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert "total_users" in data

    def test_users_list_requires_admin(self, client, citizen_token):
        resp = client.get(f"{BASE}/users",
                          headers={"Authorization": f"Bearer {citizen_token}"})
        assert resp.status_code == 403

    def test_users_list_accessible_for_admin(self, client, admin_token):
        resp = client.get(f"{BASE}/users",
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert "users" in data

    def test_audit_logs_requires_admin(self, client, citizen_token):
        resp = client.get(f"{BASE}/audit-logs",
                          headers={"Authorization": f"Bearer {citizen_token}"})
        assert resp.status_code == 403

    def test_models_list_admin_only(self, client, citizen_token, admin_token):
        citizen_resp = client.get(f"{BASE}/models",
                                  headers={"Authorization": f"Bearer {citizen_token}"})
        admin_resp = client.get(f"{BASE}/models",
                                headers={"Authorization": f"Bearer {admin_token}"})
        assert citizen_resp.status_code == 403
        assert admin_resp.status_code == 200


class TestAdminUserManagement:
    def test_update_user_role(self, client, admin_token, citizen_user):
        resp = client.put(
            f"{BASE}/users/{citizen_user.id}",
            json={"role": "researcher"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["user"]["role"] == "researcher"

    def test_update_nonexistent_user(self, client, admin_token):
        resp = client.put(
            f"{BASE}/users/99999",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404

    def test_deactivate_user(self, client, admin_token, citizen_user):
        resp = client.delete(
            f"{BASE}/users/{citizen_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
