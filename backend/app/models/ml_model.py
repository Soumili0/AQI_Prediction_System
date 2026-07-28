"""MLModel — registry of trained models and their evaluation metrics."""

from datetime import datetime
from app import db


class MLModel(db.Model):
    __tablename__ = "ml_models"

    id: int = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name: str = db.Column(db.String(100), nullable=False)
    algorithm: str = db.Column(
        db.Enum("linear_regression", "decision_tree", "random_forest",
                "xgboost", "lightgbm", "lstm"),
        nullable=False
    )
    version: str = db.Column(db.String(20), nullable=False, default="1.0.0")
    file_path: str = db.Column(db.String(512), nullable=False)
    scaler_path: str = db.Column(db.String(512), nullable=True)
    feature_names = db.Column(db.JSON, nullable=True)
    hyperparameters = db.Column(db.JSON, nullable=True)
    mae: float = db.Column(db.Float, nullable=True)
    rmse: float = db.Column(db.Float, nullable=True)
    mse: float = db.Column(db.Float, nullable=True)
    r2_score: float = db.Column(db.Float, nullable=True)
    training_time_s: float = db.Column(db.Float, nullable=True)
    train_size: int = db.Column(db.Integer, nullable=True)
    test_size: int = db.Column(db.Integer, nullable=True)
    is_active: bool = db.Column(db.Boolean, nullable=False, default=False)
    trained_by: int = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    trained_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    predictions = db.relationship("Prediction", back_populates="model", lazy="dynamic")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "algorithm": self.algorithm,
            "version": self.version,
            "metrics": {
                "mae": self.mae,
                "rmse": self.rmse,
                "mse": self.mse,
                "r2_score": self.r2_score,
            },
            "training_time_s": self.training_time_s,
            "train_size": self.train_size,
            "test_size": self.test_size,
            "is_active": self.is_active,
            "trained_at": self.trained_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<MLModel {self.name} v{self.version} active={self.is_active}>"
