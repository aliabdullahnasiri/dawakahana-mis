import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func

from app.extensions.db import db
from app.models.base import Base
from app.models.invoice_item import InvoiceItem
from app.models.transaction import Transaction, TransactionType


class InvoiceType(enum.Enum):
    PURCHASE = "PURCHASE"
    SALE = "SALE"
    PURCHASE_RETURN = "PURCHASE_RETURN"
    SALE_RETURN = "SALE_RETURN"


class InvoiceStatus(enum.Enum):
    DRAFT = "DRAFT"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Invoice(Base):

    __tablename__ = "invoices"

    invoice_number = db.Column(db.String(100), unique=True, nullable=False, index=True)

    invoice_type = db.Column(db.Enum(InvoiceType), nullable=False)

    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=True)

    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=True)

    status = db.Column(
        db.Enum(InvoiceStatus),
        nullable=False,
        default=InvoiceStatus.COMPLETED,
    )

    invoice_date = db.Column(db.DateTime, nullable=False)

    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))

    items = db.relationship(
        "InvoiceItem", back_populates="invoice", cascade="all, delete-orphan"
    )

    supplier = db.relationship("Supplier", back_populates="invoices")

    customer = db.relationship("Customer", back_populates="invoices")

    transactions = db.relationship(
        "Transaction", back_populates="invoice", lazy="dynamic"
    )

    user = db.relationship("User")

    def to_dict(self):
        return {
            "invoice_number": self.invoice_number,
            "invoice_type": self.invoice_type.value,
            "invoice_date": self.invoice_date,
            **getattr(super(), "to_dict")(),
        }

    @staticmethod
    def generate_invoice_number(invoice_type: InvoiceType) -> str:
        prefix = {
            InvoiceType.PURCHASE: "PUR",
            InvoiceType.SALE: "SAL",
            InvoiceType.PURCHASE_RETURN: "PRT",
            InvoiceType.SALE_RETURN: "SRT",
        }[invoice_type]

        date = datetime.now().strftime("%Y%m%d")

        last_invoice = (
            Invoice.query.filter(
                Invoice.invoice_type == invoice_type,
                Invoice.invoice_number.like(f"{prefix}-{date}-%"),
            )
            .order_by(Invoice.id.desc())
            .first()
        )

        if last_invoice:
            sequence = int(last_invoice.invoice_number.rsplit("-", 1)[1]) + 1
        else:
            sequence = 1

        return f"{prefix}-{date}-{sequence:04d}"

    @property
    def total_amount(self):
        return db.session.query(
            func.coalesce(
                func.sum(InvoiceItem.total_price),
                0,
            )
        ).filter(InvoiceItem.invoice_id == self.id,).scalar() or Decimal("0")

    @property
    def paid_amount(self):
        return db.session.query(
            func.coalesce(
                func.sum(Transaction.amount),
                0,
            )
        ).filter(
            Transaction.invoice_id == self.id,
            Transaction.transaction_type == TransactionType.PAYMENT,
        ).scalar() or Decimal("0")

    @property
    def remaining_amount(self):
        return max(
            self.total_amount - self.paid_amount,
            Decimal("0"),
        )
