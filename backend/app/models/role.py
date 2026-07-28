"""Role model — maps to the `roles` table."""

from datetime import datetime
from app import db


class Role(db.Model):
    """Application role (admin, researcher, policy_maker, citizen)."""

    __tablename__ = "roles"

    id: int = db.Column(db.SmallInteger, primary_key=True, autoincrement=True)
    name: str = db.Column(db.String(50), nullable=False, unique=True)
    description: str = db.Column(db.String(255), nullable=True)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    users = db.relationship("User", back_populates="role", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Role {self.name}>"

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "description": self.description}
