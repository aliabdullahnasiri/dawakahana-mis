import enum

from app.extensions.db import db
from app.models.base import Base


class TransactionType(enum.Enum):
    SALE = "SALE"
    PURCHASE = "PURCHASE"
    PAYMENT = "PAYMENT"
    PURCHASE_RETURN = "PURCHASE_RETURN"
    SALE_RETURN = "SALE_RETURN"
    ADJUSTMENT = "ADJUSTMENT"


class Transaction(Base):

    __tablename__ = "transactions"

    transaction_type = db.Column(db.Enum(TransactionType), nullable=False)

    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=True)

    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=True)

    invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"), nullable=True)

    amount = db.Column(db.Numeric(10, 2), nullable=False)

    note = db.Column(db.Text)

    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))

    created_at = db.Column(db.DateTime, server_default=db.func.now())

    customer = db.relationship("Customer", back_populates="transactions")

    supplier = db.relationship("Supplier", back_populates="transactions")

    invoice = db.relationship("Invoice")
