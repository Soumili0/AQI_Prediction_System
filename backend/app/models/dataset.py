"""Dataset model — tracks uploaded and API-fetched datasets."""

from datetime import datetime
from app import db


class Dataset(db.Model):
    __tablename__ = "datasets"

    SOURCE_CSV = "csv_upload"
    SOURCE_OPENAQ = "openaq_api"
    SOURCE_GOVERNMENT = "government"
    SOURCE_HISTORICAL = "historical"

    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_READY = "ready"
    STATUS_FAILED = "failed"

    id: int = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name: str = db.Column(db.String(255), nullable=False)
    source: str = db.Column(
        db.Enum("csv_upload", "openaq_api", "government", "historical"),
        nullable=False, default="csv_upload"
    )
    file_path: str = db.Column(db.String(512), nullable=True)
    original_filename: str = db.Column(db.String(255), nullable=True)
    file_size_kb: int = db.Column(db.Integer, nullable=True)
    row_count: int = db.Column(db.Integer, nullable=True)
    column_count: int = db.Column(db.SmallInteger, nullable=True)
    status: str = db.Column(
        db.Enum("pending", "processing", "ready", "failed"),
        nullable=False, default="pending"
    )
    processing_log: str = db.Column(db.Text, nullable=True)
    date_from = db.Column(db.Date, nullable=True)
    date_to = db.Column(db.Date, nullable=True)
    location: str = db.Column(db.String(255), nullable=True)
    description: str = db.Column(db.Text, nullable=True)
    is_public: bool = db.Column(db.Boolean, nullable=False, default=False)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user = db.relationship("User", back_populates="datasets")
    readings = db.relationship("AQIReading", back_populates="dataset", lazy="dynamic")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "source": self.source,
            "original_filename": self.original_filename,
            "file_size_kb": self.file_size_kb,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "status": self.status,
            "location": self.location,
            "date_from": self.date_from.isoformat() if self.date_from else None,
            "date_to": self.date_to.isoformat() if self.date_to else None,
            "description": self.description,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<Dataset {self.name} ({self.status})>"
