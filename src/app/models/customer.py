from app.extensions.db import db
from app.models.base import Base


class Customer(Base):

    __tablename__ = "customers"

    name = db.Column(db.String(100), nullable=False)

    phone = db.Column(db.String(50), unique=True, index=True)

    email = db.Column(db.String(120))

    address = db.Column(db.String(255))

    notes = db.Column(db.Text)

    is_active = db.Column(db.Boolean, default=True)

    invoices = db.relationship("Invoice", back_populates="customer", lazy="dynamic")

    transactions = db.relationship(
        "Transaction", back_populates="customer", lazy="dynamic"
    )

    invoices = db.relationship("Invoice", back_populates="customer", lazy="dynamic")

    def to_dict(self) -> dict:

        return {
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "notes": self.notes,
            "is_active": self.is_active,
            **getattr(super(), "to_dict")(),
        }

    def __repr__(self):
        return f"<Customer name='{self.name!r}' " f"phone='{self.phone!r}'>"
