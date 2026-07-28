"""RefreshToken model — supports JWT revocation."""

from datetime import datetime
from app import db


class RefreshToken(db.Model):
    __tablename__ = "refresh_tokens"

    id: int = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    jti: str = db.Column(db.String(36), nullable=False, unique=True, index=True)
    is_revoked: bool = db.Column(db.Boolean, nullable=False, default=False)
    expires_at: datetime = db.Column(db.DateTime, nullable=False)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="refresh_tokens")

    def revoke(self) -> None:
        self.is_revoked = True

    def is_valid(self) -> bool:
        return not self.is_revoked and self.expires_at > datetime.utcnow()

    def __repr__(self) -> str:
        return f"<RefreshToken jti={self.jti} revoked={self.is_revoked}>"
