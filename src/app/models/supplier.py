from app.extensions.db import db
from app.models.base import Base


class Supplier(Base):

    __tablename__ = "suppliers"

    name = db.Column(db.String(255), nullable=False)

    company_name = db.Column(db.String(255))

    phone = db.Column(db.String(50))

    email = db.Column(db.String(255))

    address = db.Column(db.Text)

    is_active = db.Column(db.Boolean, default=True)

    invoices = db.relationship("Invoice", back_populates="supplier", lazy="dynamic")

    transactions = db.relationship(
        "Transaction", back_populates="supplier", lazy="dynamic"
    )

    def to_dict(self):

        return {
            "name": self.name,
            "company_name": self.company_name,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "is_active": self.is_active,
            **getattr(super(), "to_dict")(),
        }
