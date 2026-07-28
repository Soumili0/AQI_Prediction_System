"""User model — maps to the `users` table."""

from datetime import datetime
from app import db, bcrypt


class User(db.Model):
    """Registered user with role-based access control."""

    __tablename__ = "users"

    id: int = db.Column(db.Integer, primary_key=True, autoincrement=True)
    role_id: int = db.Column(
        db.SmallInteger, db.ForeignKey("roles.id"), nullable=False, default=4
    )
    email: str = db.Column(db.String(255), nullable=False, unique=True, index=True)
    username: str = db.Column(db.String(100), nullable=False, unique=True, index=True)
    password_hash: str = db.Column(db.String(255), nullable=False)
    first_name: str = db.Column(db.String(100), nullable=True)
    last_name: str = db.Column(db.String(100), nullable=True)
    phone: str = db.Column(db.String(20), nullable=True)
    organization: str = db.Column(db.String(255), nullable=True)
    city: str = db.Column(db.String(100), nullable=True)
    country: str = db.Column(db.String(100), nullable=True)
    is_active: bool = db.Column(db.Boolean, nullable=False, default=True)
    is_verified: bool = db.Column(db.Boolean, nullable=False, default=False)
    avatar_url: str = db.Column(db.String(512), nullable=True)
    last_login: datetime = db.Column(db.DateTime, nullable=True)
    password_reset_token: str = db.Column(db.String(255), nullable=True)
    reset_token_expires: datetime = db.Column(db.DateTime, nullable=True)
    verify_token: str = db.Column(db.String(255), nullable=True)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    role = db.relationship("Role", back_populates="users")
    refresh_tokens = db.relationship("RefreshToken", back_populates="user", lazy="dynamic")
    datasets = db.relationship("Dataset", back_populates="user", lazy="dynamic")
    predictions = db.relationship("Prediction", back_populates="user", lazy="dynamic")
    reports = db.relationship("Report", back_populates="user", lazy="dynamic")

    # ------------------------------------------------------------------
    # Password helpers
    # ------------------------------------------------------------------
    def set_password(self, plain_password: str) -> None:
        """Hash and store password using bcrypt."""
        self.password_hash = bcrypt.generate_password_hash(plain_password).decode("utf-8")

    def check_password(self, plain_password: str) -> bool:
        """Verify a plain-text password against the stored hash."""
        return bcrypt.check_password_hash(self.password_hash, plain_password)

    # ------------------------------------------------------------------
    # Role helpers
    # ------------------------------------------------------------------
    @property
    def role_name(self) -> str:
        return self.role.name if self.role else "citizen"

    def has_role(self, *role_names: str) -> bool:
        """Return True if user's role is in the given list."""
        return self.role_name in role_names

    def is_admin(self) -> bool:
        return self.role_name == "admin"

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------
    def to_dict(self, include_private: bool = False) -> dict:
        data = {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "organization": self.organization,
            "city": self.city,
            "country": self.country,
            "role": self.role_name,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "avatar_url": self.avatar_url,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat(),
        }
        if include_private:
            data["phone"] = self.phone
        return data

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role_name})>"
