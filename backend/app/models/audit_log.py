"""AuditLog model — immutable record of security-relevant actions."""

from datetime import datetime
from app import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id: int = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action: str = db.Column(db.String(100), nullable=False, index=True)
    entity: str = db.Column(db.String(100), nullable=True)
    entity_id: str = db.Column(db.String(100), nullable=True)
    old_value = db.Column(db.JSON, nullable=True)
    new_value = db.Column(db.JSON, nullable=True)
    ip_address: str = db.Column(db.String(45), nullable=True)
    user_agent: str = db.Column(db.String(512), nullable=True)
    status: str = db.Column(db.Enum("success", "failure"), nullable=False, default="success")
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "entity": self.entity,
            "entity_id": self.entity_id,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "ip_address": self.ip_address,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} by user_id={self.user_id}>"
