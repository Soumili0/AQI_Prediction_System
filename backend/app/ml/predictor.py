"""
ML Predictor
=============
Singleton that loads the trained model, scaler, and feature list exactly once
and exposes a predict() method consumed by the prediction service.

Why singleton? Loading a 50-200 MB model on every request would be
unacceptably slow. The singleton is initialised on first use (lazy loading)
so it doesn't block application startup.
"""

import os
import json
import logging
import numpy as np
import joblib

logger = logging.getLogger(__name__)

_MODEL_INSTANCE = None


class AQIPredictor:
    """Wraps the trained model, scaler, and feature list."""

    def __init__(self, model_path: str, scaler_path: str, feature_names_path: str):
        logger.info("Loading AQI model from %s", model_path)
        self.model        = joblib.load(model_path)
        self.scaler       = joblib.load(scaler_path)
        with open(feature_names_path, "r") as f:
            self.feature_names = json.load(f)
        logger.info("Model loaded. Features: %s", self.feature_names)

    def predict(self, feature_dict: dict) -> dict:
        """Make a single AQI prediction.

        Args:
            feature_dict: dict mapping feature_name → numeric value.
                          Missing features are filled with 0.

        Returns:
            dict with predicted_aqi, feature_vector, feature_names.
        """
        # Build feature vector in correct order
        vector = np.array([
            float(feature_dict.get(f, 0) or 0)
            for f in self.feature_names
        ]).reshape(1, -1)

        scaled = self.scaler.transform(vector)
        pred   = float(self.model.predict(scaled)[0])
        pred   = max(0.0, round(pred, 2))

        return {
            "predicted_aqi": pred,
            "feature_vector": vector.flatten().tolist(),
            "feature_vector_scaled": scaled.flatten().tolist(),
            "feature_names": self.feature_names,
        }

    def predict_batch(self, records: list) -> list:
        """Predict AQI for a list of feature dicts."""
        vectors = np.array([
            [float(r.get(f, 0) or 0) for f in self.feature_names]
            for r in records
        ])
        scaled = self.scaler.transform(vectors)
        preds  = self.model.predict(scaled)
        return [max(0.0, round(float(p), 2)) for p in preds]


def get_predictor() -> AQIPredictor:
    """Return the singleton predictor, creating it on first call."""
    global _MODEL_INSTANCE
    if _MODEL_INSTANCE is None:
        from flask import current_app
        model_path   = current_app.config.get("MODEL_PATH",    "ml/models/aqi_model.pkl")
        scaler_path  = current_app.config.get("SCALER_PATH",   "ml/models/scaler.pkl")
        feature_path = current_app.config.get("FEATURE_NAMES_PATH", "ml/models/feature_names.json")

        # Resolve relative paths from project root
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
        if not os.path.isabs(model_path):
            model_path   = os.path.join(root, model_path)
        if not os.path.isabs(scaler_path):
            scaler_path  = os.path.join(root, scaler_path)
        if not os.path.isabs(feature_path):
            feature_path = os.path.join(root, feature_path)

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model file not found at {model_path}. "
                "Run `python ml/scripts/train_models.py` first."
            )
        _MODEL_INSTANCE = AQIPredictor(model_path, scaler_path, feature_path)

    return _MODEL_INSTANCE


def reset_predictor() -> None:
    """Force reload on next call (use after retraining)."""
    global _MODEL_INSTANCE
    _MODEL_INSTANCE = None
