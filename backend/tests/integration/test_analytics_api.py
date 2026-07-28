"""Integration tests — Analytics API endpoints"""

BASE = "/api/v1/analytics"


class TestAnalyticsOverview:
    def test_overview_public(self, client):
        resp = client.get(f"{BASE}/overview")
        assert resp.status_code == 200
        data = resp.get_json()
        # Should have at least these keys (even if empty DB)
        assert "message" in data or "mean_aqi" in data or "total_readings" in data

    def test_overview_with_city_param(self, client):
        resp = client.get(f"{BASE}/overview?city=Delhi&days=30")
        assert resp.status_code == 200

    def test_overview_invalid_days(self, client):
        # Should still return 200, just with 0 data
        resp = client.get(f"{BASE}/overview?days=abc")
        # days param conversion may raise 400 or return 200 with empty data
        assert resp.status_code in (200, 400)


class TestAnalyticsTrend:
    def test_trend_daily(self, client):
        resp = client.get(f"{BASE}/trend?granularity=daily&days=30")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "trend" in data
        assert isinstance(data["trend"], list)

    def test_trend_monthly(self, client):
        resp = client.get(f"{BASE}/trend?granularity=monthly&days=90")
        assert resp.status_code == 200

    def test_trend_yearly(self, client):
        resp = client.get(f"{BASE}/trend?granularity=yearly&days=365")
        assert resp.status_code == 200

    def test_trend_invalid_granularity(self, client):
        resp = client.get(f"{BASE}/trend?granularity=hourly")
        assert resp.status_code == 400


class TestAnalyticsCities:
    def test_cities_public(self, client):
        resp = client.get(f"{BASE}/cities")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "cities" in data
        assert isinstance(data["cities"], list)


class TestAnalyticsPollutants:
    def test_pollutants_public(self, client):
        resp = client.get(f"{BASE}/pollutants")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "pollutants" in data


class TestAnalyticsModels:
    def test_models_requires_auth(self, client):
        resp = client.get(f"{BASE}/models")
        assert resp.status_code == 401

    def test_models_with_auth(self, client, citizen_token):
        resp = client.get(f"{BASE}/models",
                          headers={"Authorization": f"Bearer {citizen_token}"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert "models" in data


class TestAnalyticsPredStats:
    def test_pred_stats_requires_auth(self, client):
        resp = client.get(f"{BASE}/prediction-stats")
        assert resp.status_code == 401

    def test_pred_stats_with_auth(self, client, citizen_token):
        resp = client.get(f"{BASE}/prediction-stats",
                          headers={"Authorization": f"Bearer {citizen_token}"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert "total_predictions" in data
