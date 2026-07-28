"""Prediction model — stores every AQI prediction request and result."""

from datetime import datetime
from app import db


AQI_CATEGORIES = {
    (0, 50): ("Good", "Air quality is satisfactory, and air pollution poses little or no risk."),
    (51, 100): ("Moderate", "Air quality is acceptable. Some pollutants may be a concern for very sensitive individuals."),
    (101, 150): ("Unhealthy for Sensitive Groups", "Members of sensitive groups may experience health effects. The general public is less likely to be affected."),
    (151, 200): ("Unhealthy", "Everyone may begin to experience health effects; members of sensitive groups may experience more serious effects."),
    (201, 300): ("Very Unhealthy", "Health alert: The risk of health effects is increased for everyone."),
    (301, 500): ("Hazardous", "Health warning of emergency conditions: everyone is more likely to be affected."),
}


def get_aqi_category(aqi_value: float) -> tuple:
    """Return (category_name, health_advisory) for a given AQI value."""
    for (lo, hi), (cat, advisory) in AQI_CATEGORIES.items():
        if lo <= aqi_value <= hi:
            return cat, advisory
    return "Hazardous", "Health warning of emergency conditions."


class Prediction(db.Model):
    __tablename__ = "predictions"

    id: int = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    model_id: int = db.Column(db.Integer, db.ForeignKey("ml_models.id"), nullable=True)
    city: str = db.Column(db.String(100), nullable=True)
    input_features = db.Column(db.JSON, nullable=False)
    predicted_aqi: float = db.Column(db.Float, nullable=False)
    aqi_category: str = db.Column(db.String(50), nullable=True)
    health_advisory: str = db.Column(db.Text, nullable=True)
    confidence: float = db.Column(db.Float, nullable=True)
    explanation = db.Column(db.JSON, nullable=True)
    ip_address: str = db.Column(db.String(45), nullable=True)
    requested_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = db.relationship("User", back_populates="predictions")
    model = db.relationship("MLModel", back_populates="predictions")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "city": self.city,
            "input_features": self.input_features,
            "predicted_aqi": round(self.predicted_aqi, 2),
            "aqi_category": self.aqi_category,
            "health_advisory": self.health_advisory,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "requested_at": self.requested_at.isoformat(),
            "model": self.model.name if self.model else None,
        }

    def __repr__(self) -> str:
        return f"<Prediction aqi={self.predicted_aqi:.1f} city={self.city}>"
