from operator import call

from sqlalchemy import UniqueConstraint

from app.extensions.db import db


class UserRole(db.Model):
    __tablename__ = "users_roles"

    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    __table_args__ = (UniqueConstraint("role_id", "user_id", name="uix_role_user"),)

    def to_dict(self) -> dict:
        return {
            "role_id": self.role_id,
            "user_id": self.user_id,
            **call(getattr(super(), "to_dict")),
        }

    def __repr__(self):
        return f"<UserRole role_id='{self.role_id}' user_id='{self.user_id}'>"
