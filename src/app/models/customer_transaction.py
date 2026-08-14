import enum

from app.extensions.db import db
from app.models.base import Base


class TransactionType(enum.Enum):
    SALE = "SALE"
    PAYMENT = "PAYMENT"
    RETURN = "RETURN"


class CustomerTransaction(Base):

    __tablename__ = "customer_transactions"

    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)

    invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"), nullable=True)

    transaction_type = db.Column(db.Enum(TransactionType), nullable=False)

    amount = db.Column(db.Numeric(10, 2), nullable=False)

    payment_method = db.Column(db.Enum("CASH", "CARD", "TRANSFER"), default="CASH")

    note = db.Column(db.Text)

    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))

    created_at = db.Column(db.DateTime, server_default=db.func.now())

    customer = db.relationship("Customer", back_populates="transactions")

    invoice = db.relationship("Invoice", back_populates="transactions")

    user = db.relationship("User")

    def to_dict(self):

        return {
            "customer_id": self.customer_id,
            "invoice_id": self.invoice_id,
            "transaction_type": self.transaction_type,
            "amount": self.amount,
            "payment_method": self.payment_method,
            "note": self.note,
            "created_at": self.created_at,
            **getattr(super(), "to_dict")(),
        }

    def __repr__(self):

        return (
            f"<CustomerTransaction "
            f"customer_id='{self.customer_id}' "
            f"type='{self.transaction_type}'>"
        )
