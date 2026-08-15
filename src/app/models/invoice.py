import enum
from datetime import datetime

from app.extensions.db import db
from app.models.base import Base


class InvoiceType(enum.Enum):
    PURCHASE = "PURCHASE"
    SALE = "SALE"
    PURCHASE_RETURN = "PURCHASE_RETURN"
    SALE_RETURN = "SALE_RETURN"


class PaymentStatus(enum.Enum):
    PAID = "PAID"
    PARTIAL = "PARTIAL"
    UNPAID = "UNPAID"


class Invoice(Base):

    __tablename__ = "invoices"

    invoice_number = db.Column(db.String(100), unique=True, nullable=False, index=True)

    invoice_type = db.Column(db.Enum(InvoiceType), nullable=False)

    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=True)

    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=True)

    payment_status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.UNPAID)

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
            "payment_status": self.payment_status.value,
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
