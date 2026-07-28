"""Integration tests — Prediction API endpoints"""

import pytest
from unittest.mock import patch, MagicMock

BASE = "/api/v1/predictions"

VALID_FEATURES = {
    "pm25": 85.5, "pm10": 120.0, "no2": 45.2,
    "so2": 18.3,  "co": 1.2,     "o3": 60.0,
    "temperature": 28.0, "humidity": 65.0, "city": "Delhi",
}

MOCK_PRED_RESULT = {
    "id": 1,
    "predicted_aqi": 142.5,
    "aqi_category": "Unhealthy for Sensitive Groups",
    "health_advisory": "Sensitive groups may experience health effects.",
    "input_features": VALID_FEATURES,
    "explanation": {"method": "shap", "feature_importance": {"pm25": 0.45}},
    "requested_at": "2024-01-01T12:00:00",
    "model": "XGBoost",
}


class TestPredictEndpoint:
    @patch("app.api.v1.routes.prediction.prediction_service.predict_aqi",
           return_value=MOCK_PRED_RESULT)
    def test_prediction_success(self, mock_pred, client):
        resp = client.post(f"{BASE}/", json=VALID_FEATURES)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "predicted_aqi" in data

    @patch("app.api.v1.routes.prediction.prediction_service.predict_aqi",
           side_effect=ValueError("Missing required features: ['pm25']"))
    def test_missing_required_features(self, mock_pred, client):
        resp = client.post(f"{BASE}/", json={"co": 1.0})
        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_empty_body(self, client):
        resp = client.post(f"{BASE}/", json={})
        assert resp.status_code in (400, 503)  # no model loaded in test env

    @patch("app.api.v1.routes.prediction.prediction_service.predict_aqi",
           side_effect=FileNotFoundError("Model not found"))
    def test_model_not_loaded(self, mock_pred, client):
        resp = client.post(f"{BASE}/", json=VALID_FEATURES)
        assert resp.status_code == 503

    def test_history_requires_auth(self, client):
        resp = client.get(f"{BASE}/history")
        assert resp.status_code == 401

    def test_history_with_auth(self, client, citizen_token):
        resp = client.get(f"{BASE}/history",
                          headers={"Authorization": f"Bearer {citizen_token}"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert "predictions" in data
        assert "total" in data

    def test_batch_requires_auth(self, client):
        resp = client.post(f"{BASE}/batch", json={"records": [VALID_FEATURES]})
        assert resp.status_code == 401


class TestPredictionValidation:
    @patch("app.api.v1.routes.prediction.prediction_service.predict_aqi",
           return_value=MOCK_PRED_RESULT)
    def test_negative_values_accepted_by_service(self, mock_pred, client):
        # Validation of negative values is at service layer; API should pass through
        payload = {**VALID_FEATURES, "pm25": -5.0}
        resp = client.post(f"{BASE}/", json=payload)
        assert resp.status_code == 200  # mock returns valid result

    @patch("app.api.v1.routes.prediction.prediction_service.predict_aqi",
           return_value=MOCK_PRED_RESULT)
    def test_extra_fields_ignored(self, mock_pred, client):
        payload = {**VALID_FEATURES, "unknown_field": "ignored"}
        resp = client.post(f"{BASE}/", json=payload)
        assert resp.status_code == 200
