"""AQIReading model — stores individual air quality sensor readings."""

from datetime import datetime
from app import db


class AQIReading(db.Model):
    __tablename__ = "aqi_readings"

    id: int = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    dataset_id: int = db.Column(db.Integer, db.ForeignKey("datasets.id"), nullable=True)
    station_id: str = db.Column(db.String(100), nullable=True)
    city: str = db.Column(db.String(100), nullable=False)
    country: str = db.Column(db.String(100), nullable=True)
    latitude = db.Column(db.Numeric(9, 6), nullable=True)
    longitude = db.Column(db.Numeric(9, 6), nullable=True)
    recorded_at: datetime = db.Column(db.DateTime, nullable=False, index=True)
    pm25: float = db.Column(db.Float, nullable=True)
    pm10: float = db.Column(db.Float, nullable=True)
    no2: float = db.Column(db.Float, nullable=True)
    so2: float = db.Column(db.Float, nullable=True)
    co: float = db.Column(db.Float, nullable=True)
    o3: float = db.Column(db.Float, nullable=True)
    nh3: float = db.Column(db.Float, nullable=True)
    temperature: float = db.Column(db.Float, nullable=True)
    humidity: float = db.Column(db.Float, nullable=True)
    wind_speed: float = db.Column(db.Float, nullable=True)
    wind_direction: float = db.Column(db.Float, nullable=True)
    pressure: float = db.Column(db.Float, nullable=True)
    aqi: float = db.Column(db.Float, nullable=True, index=True)
    aqi_category: str = db.Column(db.String(50), nullable=True)
    source: str = db.Column(db.String(100), nullable=True)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    dataset = db.relationship("Dataset", back_populates="readings")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "station_id": self.station_id,
            "city": self.city,
            "country": self.country,
            "latitude": float(self.latitude) if self.latitude else None,
            "longitude": float(self.longitude) if self.longitude else None,
            "recorded_at": self.recorded_at.isoformat(),
            "pm25": self.pm25, "pm10": self.pm10, "no2": self.no2,
            "so2": self.so2, "co": self.co, "o3": self.o3, "nh3": self.nh3,
            "temperature": self.temperature, "humidity": self.humidity,
            "wind_speed": self.wind_speed, "wind_direction": self.wind_direction,
            "pressure": self.pressure,
            "aqi": self.aqi, "aqi_category": self.aqi_category,
        }

    def __repr__(self) -> str:
        return f"<AQIReading city={self.city} aqi={self.aqi} at={self.recorded_at}>"
