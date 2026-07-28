"""Report model — tracks generated PDF/CSV/XLSX reports."""

from datetime import datetime
from app import db


class Report(db.Model):
    __tablename__ = "reports"

    id: int = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    title: str = db.Column(db.String(255), nullable=False)
    report_type: str = db.Column(
        db.Enum("prediction_history", "analytics", "model_comparison", "eda"),
        nullable=False
    )
    format: str = db.Column(db.Enum("pdf", "csv", "xlsx"), nullable=False, default="pdf")
    file_path: str = db.Column(db.String(512), nullable=True)
    parameters = db.Column(db.JSON, nullable=True)
    file_size_kb: int = db.Column(db.Integer, nullable=True)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="reports")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "report_type": self.report_type,
            "format": self.format,
            "file_size_kb": self.file_size_kb,
            "parameters": self.parameters,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<Report {self.title} ({self.format})>"
